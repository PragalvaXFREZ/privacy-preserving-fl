import logging
import os
import random
from typing import Dict, Optional

import torch
import torchvision.transforms as transforms
from PIL import Image

from app.ml.densenet import get_densenet121

logger = logging.getLogger(__name__)

CHESTXRAY_PATHOLOGIES = [
    "Atelectasis",
    "Cardiomegaly",
    "Effusion",
    "Infiltration",
    "Mass",
    "Nodule",
    "Pneumonia",
    "Pneumothorax",
    "Consolidation",
    "Edema",
    "Emphysema",
    "Fibrosis",
    "Pleural_Thickening",
    "Hernia",
]

INFERENCE_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


class ModelPredictor:
    """Singleton-style predictor that loads a DenseNet-121 model and runs inference.

    If the model weights file does not exist, the predictor returns mock predictions
    for demonstration purposes.
    """

    _instance: Optional["ModelPredictor"] = None

    def __new__(cls, model_path: str = "./models/global_model.pth"):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._initialized = False
            cls._instance = instance
        return cls._instance

    def __init__(self, model_path: str = "./models/global_model.pth"):
        if self._initialized:
            return
        self._initialized = True
        self.model_path = model_path
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load model weights from disk."""
        if not os.path.exists(self.model_path):
            logger.warning(
                f"Model file not found at {self.model_path}. "
                "Predictions will be mocked for demo purposes."
            )
            self.model = None
            return

        try:
            self.model = get_densenet121(num_classes=len(CHESTXRAY_PATHOLOGIES), pretrained=False)
            state_dict = torch.load(self.model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Model loaded successfully from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}. Falling back to mock predictions.")
            self.model = None

    def _preprocess_image(self, image_path: str) -> torch.Tensor:
        """Load and preprocess an image for inference."""
        image = Image.open(image_path).convert("RGB")
        tensor = INFERENCE_TRANSFORM(image)
        return tensor.unsqueeze(0)

    def _mock_predictions(self) -> Dict[str, float]:
        """Generate mock predictions for demo when no model is available."""
        predictions = {}
        for pathology in CHESTXRAY_PATHOLOGIES:
            predictions[pathology] = round(random.uniform(0.01, 0.95), 4)
        return predictions

    def predict(self, image_path: str) -> Dict[str, float]:
        """Run inference on a chest X-ray image.

        Args:
            image_path: Path to the image file.

        Returns:
            Dictionary mapping pathology names to probability scores.
        """
        if self.model is None:
            logger.info("Using mock predictions (no model loaded)")
            return self._mock_predictions()

        try:
            input_tensor = self._preprocess_image(image_path)
            input_tensor = input_tensor.to(self.device)

            with torch.no_grad():
                output = self.model(input_tensor)

            probabilities = output.squeeze().cpu().numpy()

            predictions = {}
            for i, pathology in enumerate(CHESTXRAY_PATHOLOGIES):
                predictions[pathology] = round(float(probabilities[i]), 4)

            return predictions

        except Exception as e:
            logger.error(f"Inference failed: {e}. Returning mock predictions.")
            return self._mock_predictions()
