"""
DenseNet-121 with Square Activation for Homomorphic Encryption compatibility.

Standard ReLU activations are replaced with polynomial (square) activations
so that the model can operate on encrypted data under CKKS homomorphic
encryption, which only supports addition and multiplication.

The model targets ChestX-ray14 multi-label classification (14 pathologies).
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, Iterator, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models


class SquareActivation(nn.Module):
    """Polynomial activation function: f(x) = x * x.

    This activation is compatible with Homomorphic Encryption schemes
    (e.g. CKKS) because it only requires multiplication, which is a
    natively supported operation in HE.
    """

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * x


def replace_relu_with_square(model: nn.Module) -> nn.Module:
    """Recursively replace every ``nn.ReLU`` (and ``nn.ReLU6``) in *model*
    with :class:`SquareActivation`.

    The replacement is performed **in-place** on the module tree and the
    mutated model is returned for convenience.

    Args:
        model: Any ``nn.Module`` whose sub-modules may contain ReLU layers.

    Returns:
        The same model object with all ReLU layers replaced.
    """
    for name, module in model.named_children():
        if isinstance(module, (nn.ReLU, nn.ReLU6)):
            setattr(model, name, SquareActivation())
        else:
            replace_relu_with_square(module)
    return model


class DenseNetSquare(nn.Module):
    """DenseNet-121 with square activations and a multi-label classifier head.

    The network is split into two logical parts:

    * **body** -- the convolutional feature extractor (``model.features``).
    * **head** -- the final linear classifier layer.

    This split enables *selective* homomorphic encryption: only the compact
    head (which is privacy-sensitive) is encrypted, while the much larger
    body is transmitted in plaintext.

    Args:
        num_classes: Number of output labels (default 14 for ChestX-ray14).
        pretrained: Whether to initialise from ImageNet-pretrained weights.
    """

    def __init__(self, num_classes: int = 14, pretrained: bool = True) -> None:
        super().__init__()
        self.num_classes = num_classes

        # Load the base DenseNet-121
        weights = models.DenseNet121_Weights.DEFAULT if pretrained else None
        base_model = models.densenet121(weights=weights)

        # Replace all ReLU activations with square activations for HE
        replace_relu_with_square(base_model)

        # Feature extractor (body)
        self.features = base_model.features

        # Classifier (head) -- replace the original 1000-class head
        num_features = base_model.classifier.in_features
        self.classifier = nn.Linear(num_features, num_classes)

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Run a full forward pass.

        Pipeline: features -> adaptive_avg_pool2d -> flatten -> classifier -> sigmoid

        Args:
            x: Input tensor of shape ``(B, 3, H, W)``.

        Returns:
            Tensor of shape ``(B, num_classes)`` with values in ``[0, 1]``.
        """
        features = self.features(x)
        out = F.adaptive_avg_pool2d(features, (1, 1))
        out = torch.flatten(out, 1)
        out = self.classifier(out)
        out = torch.sigmoid(out)
        return out

    # ------------------------------------------------------------------
    # Body / Head property accessors
    # ------------------------------------------------------------------

    @property
    def body(self) -> nn.Module:
        """The convolutional feature extractor (DenseNet features)."""
        return self.features

    @property
    def head(self) -> nn.Module:
        """The linear classifier layer."""
        return self.classifier

    # ------------------------------------------------------------------
    # Parameter access helpers
    # ------------------------------------------------------------------

    def get_body_params(self) -> Iterator[Tuple[str, nn.Parameter]]:
        """Yield ``(name, param)`` pairs for the feature extractor."""
        for name, param in self.features.named_parameters():
            yield (f"features.{name}", param)

    def get_head_params(self) -> Iterator[Tuple[str, nn.Parameter]]:
        """Yield ``(name, param)`` pairs for the classifier head."""
        for name, param in self.classifier.named_parameters():
            yield (f"classifier.{name}", param)

    # ------------------------------------------------------------------
    # State-dict helpers for selective encryption
    # ------------------------------------------------------------------

    def get_body_state_dict(self) -> OrderedDict:
        """Return a state dict containing only the body (features) parameters."""
        return OrderedDict(
            (f"features.{k}", v)
            for k, v in self.features.state_dict().items()
        )

    def get_head_state_dict(self) -> OrderedDict:
        """Return a state dict containing only the head (classifier) parameters."""
        return OrderedDict(
            (f"classifier.{k}", v)
            for k, v in self.classifier.state_dict().items()
        )

    def load_body_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """Load parameters into the body only.

        Keys in *state_dict* must be prefixed with ``features.``.
        """
        body_sd = OrderedDict()
        for k, v in state_dict.items():
            # Strip the 'features.' prefix if present
            key = k.replace("features.", "", 1) if k.startswith("features.") else k
            body_sd[key] = v
        self.features.load_state_dict(body_sd, strict=True)

    def load_head_state_dict(self, state_dict: Dict[str, torch.Tensor]) -> None:
        """Load parameters into the head only.

        Keys in *state_dict* must be prefixed with ``classifier.``.
        """
        head_sd = OrderedDict()
        for k, v in state_dict.items():
            key = k.replace("classifier.", "", 1) if k.startswith("classifier.") else k
            head_sd[key] = v
        self.classifier.load_state_dict(head_sd, strict=True)
