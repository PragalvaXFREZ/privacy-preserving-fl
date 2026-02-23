from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client_update import ClientUpdate
from app.models.round_metric import RoundMetric
from app.models.training_round import TrainingRound
from app.models.user import User
from app.schemas.training import (
    ClientUpdateResponse,
    RoundDetailResponse,
    TrainingRoundResponse,
)
from app.utils.security import get_current_user

router = APIRouter(prefix="/training", tags=["Training"])


@router.get("/rounds", response_model=List[TrainingRoundResponse])
def list_rounds(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all training rounds with pagination."""
    rounds = (
        db.query(TrainingRound)
        .order_by(TrainingRound.round_number.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rounds


@router.get("/rounds/current", response_model=TrainingRoundResponse)
def get_current_round(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the currently active training round."""
    active_round = (
        db.query(TrainingRound)
        .filter(TrainingRound.status.in_(["in_progress", "aggregating"]))
        .order_by(TrainingRound.round_number.desc())
        .first()
    )
    if not active_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training round",
        )
    return active_round


@router.get("/rounds/{round_id}", response_model=RoundDetailResponse)
def get_round_detail(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get detailed information about a specific training round."""
    training_round = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
    if not training_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training round not found",
        )

    updates = (
        db.query(ClientUpdate)
        .filter(ClientUpdate.round_id == round_id)
        .all()
    )

    metric = (
        db.query(RoundMetric)
        .filter(RoundMetric.round_id == round_id)
        .first()
    )

    return RoundDetailResponse(
        id=training_round.id,
        round_number=training_round.round_number,
        job_id=training_round.job_id,
        status=training_round.status,
        num_clients=training_round.num_clients,
        started_at=training_round.started_at,
        completed_at=training_round.completed_at,
        global_loss=training_round.global_loss,
        global_auc=training_round.global_auc,
        updates=updates,
        metric=metric,
    )


@router.get("/rounds/{round_id}/updates", response_model=List[ClientUpdateResponse])
def get_round_updates(
    round_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all client updates for a specific training round."""
    training_round = db.query(TrainingRound).filter(TrainingRound.id == round_id).first()
    if not training_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training round not found",
        )

    updates = (
        db.query(ClientUpdate)
        .filter(ClientUpdate.round_id == round_id)
        .all()
    )
    return updates
