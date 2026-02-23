import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.inference_log import InferenceLog
from app.models.user import User
from app.schemas.inference import PredictionResponse
from app.services import inference_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/inference", tags=["Inference"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run inference on an uploaded chest X-ray image."""
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    with open(file_path, "wb") as f:
        contents = file.file.read()
        f.write(contents)

    log_entry = inference_service.run_inference(
        db=db,
        user=current_user,
        image_path=file_path,
        image_filename=unique_filename,
    )

    return log_entry


@router.get("/history", response_model=List[PredictionResponse])
def get_inference_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the inference history for the current user."""
    logs = (
        db.query(InferenceLog)
        .filter(InferenceLog.user_id == current_user.id)
        .order_by(InferenceLog.created_at.desc())
        .all()
    )
    return logs


@router.get("/{inference_id}", response_model=PredictionResponse)
def get_inference_detail(
    inference_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific inference log by ID."""
    log_entry = db.query(InferenceLog).filter(InferenceLog.id == inference_id).first()
    if not log_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inference log not found",
        )
    return log_entry
