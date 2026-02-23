from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.metrics import RoundMetricResponse


class TrainingRoundResponse(BaseModel):
    id: int
    round_number: int
    job_id: Optional[str] = None
    status: str
    num_clients: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    global_loss: Optional[float] = None
    global_auc: Optional[float] = None

    model_config = {"from_attributes": True}


class ClientUpdateResponse(BaseModel):
    id: int
    round_id: int
    client_id: int
    local_loss: Optional[float] = None
    local_auc: Optional[float] = None
    num_samples: Optional[int] = None
    euclidean_distance: Optional[float] = None
    encryption_status: Optional[str] = None
    submitted_at: datetime

    model_config = {"from_attributes": True}


class RoundDetailResponse(BaseModel):
    id: int
    round_number: int
    job_id: Optional[str] = None
    status: str
    num_clients: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    global_loss: Optional[float] = None
    global_auc: Optional[float] = None
    updates: List[ClientUpdateResponse] = []
    metric: Optional[RoundMetricResponse] = None

    model_config = {"from_attributes": True}
