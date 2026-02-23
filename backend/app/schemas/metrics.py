from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OverviewResponse(BaseModel):
    total_rounds: int
    active_clients: int
    latest_auc: Optional[float] = None
    flagged_clients: int
    current_round_status: Optional[str] = None


class AUCHistoryItem(BaseModel):
    round_number: int
    global_auc: Optional[float] = None


class LossHistoryItem(BaseModel):
    round_number: int
    global_loss: Optional[float] = None


class AggregationStatsResponse(BaseModel):
    round_number: int
    aggregation_method: Optional[str] = None
    weiszfeld_iterations: Optional[int] = None
    aggregation_time_ms: Optional[int] = None
    encryption_overhead_ms: Optional[int] = None


class RoundMetricResponse(BaseModel):
    id: int
    round_id: int
    aggregation_method: Optional[str] = None
    weiszfeld_iterations: Optional[int] = None
    convergence_epsilon: Optional[float] = None
    encryption_overhead_ms: Optional[int] = None
    aggregation_time_ms: Optional[int] = None
    poisoned_clients_detected: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PrivacyMetricsResponse(BaseModel):
    encryption_coverage_pct: float
    dp_epsilon: float
    dp_delta: float
    avg_noise_magnitude: float
