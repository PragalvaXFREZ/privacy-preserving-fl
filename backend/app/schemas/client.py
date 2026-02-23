from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ClientResponse(BaseModel):
    id: int
    name: str
    client_id: str
    description: Optional[str] = None
    data_profile: Optional[str] = None
    status: str
    last_heartbeat: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientStatusUpdate(BaseModel):
    status: str = Field(..., description="New status for the client")


class ClientWithTrust(ClientResponse):
    trust_score: Optional[float] = None
    is_flagged: bool = False
