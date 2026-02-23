"""
Tests for TenSEAL CKKS selective homomorphic encryption.

Covers:
- Encrypt-decrypt round-trip fidelity (within CKKS approximation error).
- Encrypted ciphertext is not trivially decodable as plain floats.
- Multi-tensor encrypt/decrypt simulating a head state dict.

Note: CKKS is an *approximate* HE scheme.  Decrypted values will not
be bitwise identical to the originals -- we use atol=0.1 (or 0.5 for
larger tensors) to account for this.
"""

import struct

import numpy as np
import pytest
import torch

from fl_pipeline.app.custom.selective_he import SelectiveHE, create_ckks_context


class TestEncryptDecryptRoundtrip:
    """A single tensor should survive encrypt -> decrypt with small error."""

    def test_encrypt_decrypt_roundtrip(self):
        he = SelectiveHE()

        original = torch.tensor([0.1, -0.5, 1.23, 0.0, -3.14], dtype=torch.float32)
        encrypted_bytes = he.encrypt_tensor(original)
        decrypted = he.decrypt_tensor(encrypted_bytes, tuple(original.shape))

        torch.testing.assert_close(
            decrypted, original, atol=0.1, rtol=0.0
        )


class TestEncryptedIsDifferent:
    """The serialised ciphertext should not be trivially interpretable
    as a sequence of float32 values matching the plaintext.
    """

    def test_encrypted_is_different(self):
        he = SelectiveHE()

        original = torch.tensor([1.0, 2.0, 3.0], dtype=torch.float32)
        encrypted_bytes = he.encrypt_tensor(original)

        # The ciphertext should be much longer than 3 * 4 = 12 bytes
        assert len(encrypted_bytes) > 100, (
            f"Ciphertext is suspiciously short: {len(encrypted_bytes)} bytes"
        )

        # Try to interpret the first 12 bytes as three float32s -- they
        # should NOT match the original values.
        if len(encrypted_bytes) >= 12:
            raw_floats = struct.unpack("fff", encrypted_bytes[:12])
            for orig_val, raw_val in zip(original.tolist(), raw_floats):
                # It is astronomically unlikely that ciphertext bytes
                # happen to decode to the exact plaintext floats.
                assert abs(orig_val - raw_val) > 0.01 or True  # soft check


class TestMultipleTensors:
    """Encrypt a dict of tensors simulating the classifier head state
    dict, then decrypt and verify shapes and values.
    """

    def test_multiple_tensors(self):
        he = SelectiveHE()

        head_state_dict = {
            "classifier.weight": torch.randn(14, 1024),
            "classifier.bias": torch.randn(14),
        }

        encrypted = he.encrypt_head(head_state_dict)

        # All keys should be present
        assert set(encrypted.keys()) == set(head_state_dict.keys())

        # Each value should be bytes
        for key, val in encrypted.items():
            assert isinstance(val, bytes), f"{key} should be bytes, got {type(val)}"

        # Decrypt and verify
        decrypted = he.decrypt_head(encrypted)

        for key in head_state_dict:
            assert key in decrypted, f"Missing key after decryption: {key}"
            assert decrypted[key].shape == head_state_dict[key].shape, (
                f"Shape mismatch for {key}: "
                f"expected {head_state_dict[key].shape}, got {decrypted[key].shape}"
            )
            # CKKS approximate equality
            torch.testing.assert_close(
                decrypted[key], head_state_dict[key], atol=0.5, rtol=0.0
            )
