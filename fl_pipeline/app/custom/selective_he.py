"""
Selective Homomorphic Encryption using TenSEAL CKKS.

Only the *classifier head* of the model is encrypted, keeping the
communication overhead manageable while protecting the privacy-sensitive
layer that most directly encodes patient-level information.

The CKKS scheme supports approximate arithmetic on encrypted floating-point
numbers, making it suitable for neural-network weight aggregation.
"""

from __future__ import annotations

import io
from typing import Dict, Optional, Tuple

import tenseal as ts
import torch


def create_ckks_context() -> ts.Context:
    """Create and return a TenSEAL CKKS encryption context.

    Parameters chosen for a balance between security and performance:

    * ``poly_modulus_degree = 8192`` -- ~128-bit security.
    * ``coeff_mod_bit_sizes = [60, 40, 40, 60]`` -- supports one
      multiplication depth, sufficient for weighted averaging.
    * ``global_scale = 2**40`` -- precision for float32 weights.

    Returns:
        A ready-to-use :class:`tenseal.Context`.
    """
    context = ts.context(
        ts.SCHEME_TYPE.CKKS,
        poly_modulus_degree=8192,
        coeff_mod_bit_sizes=[60, 40, 40, 60],
    )
    context.global_scale = 2**40
    context.generate_galois_keys()
    return context


class SelectiveHE:
    """Encrypt / decrypt model head parameters with CKKS.

    The class maintains a mapping from parameter names to their original
    tensor shapes so that decrypted flat vectors can be faithfully
    reshaped back into the correct dimensions.

    Args:
        context: An existing TenSEAL CKKS context.  If *None*, a new
            context is created via :func:`create_ckks_context`.
    """

    def __init__(self, context: Optional[ts.Context] = None) -> None:
        self.context: ts.Context = context or create_ckks_context()
        # Stores {param_name: original_shape} so we can reconstruct after decryption
        self._shapes: Dict[str, torch.Size] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def encrypt_head(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, bytes]:
        """Encrypt every tensor in *state_dict* (the classifier head).

        Each tensor is flattened to a 1-D list, encrypted as a
        :class:`tenseal.CKKSVector`, and serialised to ``bytes``.

        Args:
            state_dict: Mapping of parameter names to ``torch.Tensor`` values.

        Returns:
            A dict mapping the same parameter names to encrypted byte strings.
        """
        encrypted: Dict[str, bytes] = {}
        for name, tensor in state_dict.items():
            self._shapes[name] = tensor.shape
            encrypted[name] = self.encrypt_tensor(tensor)
        return encrypted

    def decrypt_head(self, encrypted_dict: Dict[str, bytes]) -> Dict[str, torch.Tensor]:
        """Decrypt an encrypted head back into ``torch.Tensor`` values.

        The original tensor shapes are recovered from the internal shape
        cache that was populated during :meth:`encrypt_head`.

        Args:
            encrypted_dict: Mapping of parameter names to encrypted bytes.

        Returns:
            A dict mapping parameter names to reconstructed tensors.
        """
        decrypted: Dict[str, torch.Tensor] = {}
        for name, enc_bytes in encrypted_dict.items():
            shape = self._shapes.get(name)
            if shape is None:
                raise ValueError(
                    f"No recorded shape for parameter '{name}'. "
                    "Make sure encrypt_head() was called first, or "
                    "use decrypt_tensor() directly with an explicit shape."
                )
            decrypted[name] = self.decrypt_tensor(enc_bytes, tuple(shape))
        return decrypted

    def encrypt_tensor(self, tensor: torch.Tensor) -> bytes:
        """Encrypt a single tensor and return the serialised ciphertext.

        Args:
            tensor: An arbitrary-shaped ``torch.Tensor``.

        Returns:
            Serialised :class:`tenseal.CKKSVector` as ``bytes``.
        """
        flat = tensor.detach().cpu().float().flatten().tolist()
        encrypted_vector = ts.ckks_vector(self.context, flat)
        return encrypted_vector.serialize()

    def decrypt_tensor(self, encrypted_bytes: bytes, shape: Tuple[int, ...]) -> torch.Tensor:
        """Decrypt serialised bytes back into a ``torch.Tensor``.

        Args:
            encrypted_bytes: Output of :meth:`encrypt_tensor`.
            shape: The desired output tensor shape.

        Returns:
            A ``torch.Tensor`` of the given shape.
        """
        encrypted_vector = ts.lazy_ckks_vector_from(encrypted_bytes)
        encrypted_vector.link_context(self.context)
        decrypted_flat = encrypted_vector.decrypt()
        # Only take the number of elements we need (CKKS may pad)
        import math
        num_elements = math.prod(shape)
        decrypted_flat = decrypted_flat[:num_elements]
        return torch.tensor(decrypted_flat, dtype=torch.float32).reshape(shape)

    def serialize_context(self) -> bytes:
        """Serialise the TenSEAL context (including secret key).

        This is useful for transmitting the context to a trusted server
        that needs to perform encrypted aggregation.

        Returns:
            The serialised context as ``bytes``.
        """
        return self.context.serialize(save_secret_key=True)

    # ------------------------------------------------------------------
    # Shape management helpers
    # ------------------------------------------------------------------

    def register_shapes(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """Pre-register tensor shapes without encrypting.

        Useful when the receiver needs to know shapes before decryption
        but did not perform the encryption itself.

        Args:
            state_dict: A dict mapping parameter names to tensors whose
                shapes should be recorded.
        """
        for name, tensor in state_dict.items():
            self._shapes[name] = tensor.shape

    def get_shapes(self) -> Dict[str, torch.Size]:
        """Return the currently registered shape mapping."""
        return dict(self._shapes)

    def set_shapes(self, shapes: Dict[str, Tuple[int, ...]]) -> None:
        """Manually set the shape mapping (e.g. received from the encryptor).

        Args:
            shapes: Mapping of parameter names to shape tuples.
        """
        self._shapes = {k: torch.Size(v) for k, v in shapes.items()}
