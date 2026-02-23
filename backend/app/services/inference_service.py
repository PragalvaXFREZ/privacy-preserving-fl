import os
import time
from typing import Dict

from PIL import Image
from sqlalchemy.orm import Session

from app.config import settings
from app.ml.predictor import ModelPredictor
from app.models.inference_log import InferenceLog
from app.models.user import User

_predictor: ModelPredictor = None


def _get_predictor() -> ModelPredictor:
    """Get or initialize the singleton model predictor."""
    global _predictor
    if _predictor is None:
        _predictor = ModelPredictor(model_path=settings.MODEL_PATH)
    return _predictor


def run_inference(
    db: Session,
    user: User,
    image_path: str,
    image_filename: str,
) -> InferenceLog:
    """
    Run inference on a chest X-ray image.

    Loads the model, preprocesses the image, runs prediction,
    and saves the result to the database.
    """
    predictor = _get_predictor()

    start_time = time.time()
    predictions = predictor.predict(image_path)
    elapsed_ms = int((time.time() - start_time) * 1000)

    top_finding = max(predictions, key=predictions.get)
    top_confidence = predictions[top_finding]

    model_version = "densenet121-federated-v1"
    if not os.path.exists(settings.MODEL_PATH):
        model_version = "demo-mock-v0"

    log_entry = InferenceLog(
        user_id=user.id,
        model_version=model_version,
        image_filename=image_filename,
        predictions=predictions,
        top_finding=top_finding,
        confidence=round(top_confidence, 4),
        inference_time_ms=elapsed_ms,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)

    return log_entry
