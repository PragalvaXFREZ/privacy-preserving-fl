from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client import Client
from app.models.user import User
from app.schemas.client import ClientResponse, ClientStatusUpdate, ClientWithTrust
from app.services.trust_score_service import get_latest_trust_score, get_trust_timeline
from app.utils.security import get_current_user

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/", response_model=List[ClientWithTrust])
def list_clients(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all federated learning clients, enriched with their latest trust score."""
    clients = db.query(Client).order_by(Client.created_at.desc()).all()
    results = []
    for client in clients:
        latest_trust = get_latest_trust_score(db, client.id)
        results.append(
            ClientWithTrust(
                id=client.id,
                name=client.name,
                client_id=client.client_id,
                description=client.description,
                data_profile=client.data_profile,
                status=client.status,
                last_heartbeat=client.last_heartbeat,
                created_at=client.created_at,
                trust_score=latest_trust.score if latest_trust else None,
                is_flagged=latest_trust.is_flagged if latest_trust else False,
            )
        )
    return results


@router.get("/{client_id}", response_model=ClientWithTrust)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific client's details along with latest trust info."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    latest_trust = get_latest_trust_score(db, client.id)
    return ClientWithTrust(
        id=client.id,
        name=client.name,
        client_id=client.client_id,
        description=client.description,
        data_profile=client.data_profile,
        status=client.status,
        last_heartbeat=client.last_heartbeat,
        created_at=client.created_at,
        trust_score=latest_trust.score if latest_trust else None,
        is_flagged=latest_trust.is_flagged if latest_trust else False,
    )


@router.get("/{client_id}/trust")
def get_client_trust_timeline(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the trust score timeline for a specific client."""
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )
    timeline = get_trust_timeline(db, client.id)
    return [
        {
            "round_id": ts.round_id,
            "score": ts.score,
            "deviation_avg": ts.deviation_avg,
            "is_flagged": ts.is_flagged,
            "computed_at": ts.computed_at.isoformat() if ts.computed_at else None,
        }
        for ts in timeline
    ]


@router.patch("/{client_id}/status", response_model=ClientResponse)
def update_client_status(
    client_id: int,
    status_update: ClientStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a client's status. Only admins can perform this action."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update client status",
        )

    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    client.status = status_update.status
    db.commit()
    db.refresh(client)
    return client
