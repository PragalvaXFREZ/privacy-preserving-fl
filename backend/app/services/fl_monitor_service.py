from typing import List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.round_metric import RoundMetric
from app.models.training_round import TrainingRound
from app.models.trust_score import TrustScore
from app.schemas.metrics import (
    AggregationStatsResponse,
    AUCHistoryItem,
    LossHistoryItem,
    OverviewResponse,
)


def get_overview(db: Session) -> OverviewResponse:
    """Get dashboard overview metrics."""
    total_rounds = db.query(TrainingRound).count()

    active_clients = db.query(Client).filter(Client.status == "online").count()

    latest_round = (
        db.query(TrainingRound)
        .filter(TrainingRound.global_auc.isnot(None))
        .order_by(desc(TrainingRound.round_number))
        .first()
    )
    latest_auc = latest_round.global_auc if latest_round else None

    flagged_clients = db.query(TrustScore).filter(TrustScore.is_flagged == True).distinct(TrustScore.client_id).count()

    current_round = (
        db.query(TrainingRound)
        .filter(TrainingRound.status.in_(["in_progress", "aggregating", "pending"]))
        .order_by(desc(TrainingRound.round_number))
        .first()
    )
    current_round_status = current_round.status if current_round else None

    return OverviewResponse(
        total_rounds=total_rounds,
        active_clients=active_clients,
        latest_auc=latest_auc,
        flagged_clients=flagged_clients,
        current_round_status=current_round_status,
    )


def get_auc_history(db: Session) -> List[AUCHistoryItem]:
    """Get AUC history across all completed rounds."""
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


def get_loss_history(db: Session) -> List[LossHistoryItem]:
    """Get loss history across all completed rounds."""
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


def get_aggregation_stats(db: Session) -> List[AggregationStatsResponse]:
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
