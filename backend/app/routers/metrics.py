from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.round_metric import RoundMetric
from app.models.training_round import TrainingRound
from app.models.user import User
from app.schemas.metrics import (
    AggregationStatsResponse,
    AUCHistoryItem,
    LossHistoryItem,
    OverviewResponse,
    PrivacyMetricsResponse,
)
from app.services import fl_monitor_service
from app.utils.security import get_current_user

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard overview metrics."""
    return fl_monitor_service.get_overview(db)


@router.get("/auc-history", response_model=List[AUCHistoryItem])
def get_auc_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AUC history across all training rounds."""
    rounds = (
        db.query(TrainingRound)
        .filter(TrainingRound.global_auc.isnot(None))
        .order_by(TrainingRound.round_number)
        .all()
    )
    return [
        AUCHistoryItem(round_number=r.round_number, global_auc=r.global_auc)
        for r in rounds
    ]


@router.get("/loss-history", response_model=List[LossHistoryItem])
def get_loss_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get loss history across all training rounds."""
    rounds = (
        db.query(TrainingRound)
        .filter(TrainingRound.global_loss.isnot(None))
        .order_by(TrainingRound.round_number)
        .all()
    )
    return [
        LossHistoryItem(round_number=r.round_number, global_loss=r.global_loss)
        for r in rounds
    ]


@router.get("/aggregation", response_model=List[AggregationStatsResponse])
def get_aggregation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get aggregation statistics for each round that has metrics."""
    results = (
        db.query(
            TrainingRound.round_number,
            RoundMetric.aggregation_method,
            RoundMetric.weiszfeld_iterations,
            RoundMetric.aggregation_time_ms,
            RoundMetric.encryption_overhead_ms,
        )
        .join(RoundMetric, RoundMetric.round_id == TrainingRound.id)
        .order_by(TrainingRound.round_number)
        .all()
    )

    return [
        AggregationStatsResponse(
            round_number=row.round_number,
            aggregation_method=row.aggregation_method,
            weiszfeld_iterations=row.weiszfeld_iterations,
            aggregation_time_ms=row.aggregation_time_ms,
            encryption_overhead_ms=row.encryption_overhead_ms,
        )
        for row in results
    ]


@router.get("/privacy", response_model=PrivacyMetricsResponse)
def get_privacy_metrics(
    current_user: User = Depends(get_current_user),
):
    """Get privacy-related metrics for the federated learning system."""
    return PrivacyMetricsResponse(
        encryption_coverage_pct=50.0,
        dp_epsilon=1.0,
        dp_delta=1e-5,
        avg_noise_magnitude=0.01,
    )
