from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.client_update import ClientUpdate
from app.models.training_round import TrainingRound

router = APIRouter(prefix="/internal", tags=["Internal"])


class RoundReport(BaseModel):
    round_number: int
    job_id: Optional[str] = None
    status: str
    num_clients: Optional[int] = None
    global_loss: Optional[float] = None
    global_auc: Optional[float] = None


class ClientUpdateReport(BaseModel):
    round_number: int
    client_id: str
    local_loss: Optional[float] = None
    local_auc: Optional[float] = None
    num_samples: Optional[int] = None
    euclidean_distance: Optional[float] = None
    encryption_status: Optional[str] = None


class HeartbeatReport(BaseModel):
    client_id: str
    status: str


@router.post("/round")
def report_round(
    report: RoundReport,
    db: Session = Depends(get_db),
):
    """Upsert a training round report from NVFlare."""
    training_round = (
        db.query(TrainingRound)
        .filter(TrainingRound.round_number == report.round_number)
        .first()
    )

    if training_round:
        training_round.status = report.status
        if report.job_id is not None:
            training_round.job_id = report.job_id
        if report.num_clients is not None:
            training_round.num_clients = report.num_clients
        if report.global_loss is not None:
            training_round.global_loss = report.global_loss
        if report.global_auc is not None:
            training_round.global_auc = report.global_auc
        if report.status == "in_progress" and training_round.started_at is None:
            training_round.started_at = datetime.utcnow()
        if report.status == "completed" and training_round.completed_at is None:
            training_round.completed_at = datetime.utcnow()
    else:
        training_round = TrainingRound(
            round_number=report.round_number,
            job_id=report.job_id,
            status=report.status,
            num_clients=report.num_clients,
            global_loss=report.global_loss,
            global_auc=report.global_auc,
        )
        if report.status == "in_progress":
            training_round.started_at = datetime.utcnow()
        if report.status == "completed":
            training_round.completed_at = datetime.utcnow()
        db.add(training_round)

    db.commit()
    db.refresh(training_round)
    return {"status": "ok", "round_id": training_round.id}


@router.post("/client-update")
def report_client_update(
    report: ClientUpdateReport,
    db: Session = Depends(get_db),
):
    """Record a client update for a training round from NVFlare."""
    training_round = (
        db.query(TrainingRound)
        .filter(TrainingRound.round_number == report.round_number)
        .first()
    )
    if not training_round:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Training round {report.round_number} not found",
        )

    client = (
        db.query(Client)
        .filter(Client.client_id == report.client_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with client_id '{report.client_id}' not found",
        )

    client_update = ClientUpdate(
        round_id=training_round.id,
        client_id=client.id,
        local_loss=report.local_loss,
        local_auc=report.local_auc,
        num_samples=report.num_samples,
        euclidean_distance=report.euclidean_distance,
        encryption_status=report.encryption_status,
    )
    db.add(client_update)
    db.commit()
    db.refresh(client_update)
    return {"status": "ok", "update_id": client_update.id}


@router.post("/heartbeat")
def report_heartbeat(
    report: HeartbeatReport,
    db: Session = Depends(get_db),
):
    """Update client heartbeat and status from NVFlare."""
    client = (
        db.query(Client)
        .filter(Client.client_id == report.client_id)
        .first()
    )
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with client_id '{report.client_id}' not found",
        )

    client.last_heartbeat = datetime.utcnow()
    client.status = report.status
    db.commit()
    db.refresh(client)
    return {"status": "ok", "client_id": client.id}
