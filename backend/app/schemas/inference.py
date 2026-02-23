from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class PredictionResponse(BaseModel):
    id: int
    image_filename: Optional[str] = None
    predictions: Optional[Dict] = None
    top_finding: Optional[str] = None
    confidence: Optional[float] = None
    inference_time_ms: Optional[int] = None
    model_version: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InferenceHistoryResponse(BaseModel):
    items: List[PredictionResponse] = []
    total: int
