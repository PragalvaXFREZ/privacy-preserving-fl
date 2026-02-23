import torch
import torch.nn as nn
from torchvision import models


class SquareActivation(nn.Module):
    """Custom activation function: f(x) = x * x.

    Used as a privacy-friendly replacement for ReLU in federated learning
    contexts, as polynomial activations are more compatible with homomorphic
    encryption schemes.
    """

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * x


def replace_relu_with_square(model: nn.Module) -> nn.Module:
    """Recursively replace all ReLU activations in a model with SquareActivation.

    Args:
        model: A PyTorch module whose ReLU layers will be replaced.

    Returns:
        The modified model with SquareActivation in place of ReLU.
    """
    for name, child in model.named_children():
        if isinstance(child, nn.ReLU):
            setattr(model, name, SquareActivation())
        else:
            replace_relu_with_square(child)
    return model


def get_densenet121(num_classes: int = 14, pretrained: bool = False) -> nn.Module:
    """Create a modified DenseNet-121 for chest X-ray pathology classification.

    The model is modified in two ways:
    1. All ReLU activations are replaced with SquareActivation for HE compatibility.
    2. The classifier head is replaced with a Linear layer followed by Sigmoid
       to output probabilities for each of the pathology classes.

    Args:
        num_classes: Number of output pathology classes (default 14).
        pretrained: Whether to load ImageNet pretrained weights before modification.

    Returns:
        A modified DenseNet-121 model.
    """
    weights = models.DenseNet121_Weights.DEFAULT if pretrained else None
    model = models.densenet121(weights=weights)

    model = replace_relu_with_square(model)

    num_features = model.classifier.in_features
    model.classifier = nn.Sequential(
        nn.Linear(num_features, num_classes),
        nn.Sigmoid(),
    )

    return model
