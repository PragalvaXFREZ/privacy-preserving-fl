"""
Tests for DenseNet-121 with Square Activation.

Covers:
- SquareActivation forward pass (f(x) = x^2).
- SquareActivation backward pass (gradient = 2*x).
- Full model output shape for a batch of chest X-ray images.
- Output range (sigmoid ensures [0, 1]).
- Head/body parameter split covers all model parameters.
"""

import pytest
import torch
import torch.nn as nn

from fl_pipeline.app.custom.densenet_square import (
    DenseNetSquare,
    SquareActivation,
)


class TestSquareActivation:
    """Unit tests for the SquareActivation module."""

    def test_square_activation_forward(self):
        """f([-2, -1, 0, 1, 2]) should be [4, 1, 0, 1, 4]."""
        act = SquareActivation()
        x = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0])
        y = act(x)
        expected = torch.tensor([4.0, 1.0, 0.0, 1.0, 4.0])
        torch.testing.assert_close(y, expected)

    def test_square_activation_backward(self):
        """The gradient of x^2 is 2*x."""
        act = SquareActivation()
        x = torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0], requires_grad=True)
        y = act(x)
        # Sum to get a scalar for backward
        y.sum().backward()

        expected_grad = 2.0 * torch.tensor([-2.0, -1.0, 0.0, 1.0, 2.0])
        torch.testing.assert_close(x.grad, expected_grad)


class TestDenseNetSquareModel:
    """Integration tests for the full DenseNetSquare model."""

    @pytest.fixture(scope="class")
    def model(self):
        """Create a non-pretrained model (faster for tests)."""
        return DenseNetSquare(num_classes=14, pretrained=False)

    def test_output_shape(self, model):
        """A batch of 2 images of size 224x224 should produce (2, 14) output."""
        x = torch.randn(2, 3, 224, 224)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (2, 14), f"Expected (2, 14), got {out.shape}"

    def test_output_range(self, model):
        """All outputs should be in [0, 1] due to the final sigmoid layer."""
        x = torch.randn(2, 3, 224, 224)
        with torch.no_grad():
            out = model(x)
        assert (out >= 0.0).all(), "Found output values < 0"
        assert (out <= 1.0).all(), "Found output values > 1"

    def test_head_body_split(self, model):
        """get_head_params() and get_body_params() should together cover
        every parameter in the model (no missing, no duplicates).
        """
        body_names = set()
        for name, _ in model.get_body_params():
            body_names.add(name)

        head_names = set()
        for name, _ in model.get_head_params():
            head_names.add(name)

        all_names = set()
        for name, _ in model.named_parameters():
            all_names.add(name)

        combined = body_names | head_names

        # Every model parameter should appear in exactly one of the two sets
        assert combined == all_names, (
            f"Missing params: {all_names - combined}, "
            f"Extra params: {combined - all_names}"
        )

        # No overlap between head and body
        overlap = body_names & head_names
        assert len(overlap) == 0, f"Overlapping params: {overlap}"
