import math
from datetime import datetime
from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.client_update import ClientUpdate
from app.models.training_round import TrainingRound
from app.models.trust_score import TrustScore


def compute_trust_score(
    db: Session,
    client_id: int,
    round_id: int,
) -> TrustScore:
    """
    Compute a trust score for a client in a given round.

    The trust score is based on the euclidean distance of the client's update
    from the average of all client updates in the same round. Clients with
    significantly higher deviation are flagged.
    """
    client_update = (
        db.query(ClientUpdate)
        .filter(ClientUpdate.client_id == client_id, ClientUpdate.round_id == round_id)
        .first()
    )

    if not client_update:
        score_entry = TrustScore(
            client_id=client_id,
            round_id=round_id,
            score=0.5,
            deviation_avg=None,
            is_flagged=True,
        )
        db.add(score_entry)
        db.commit()
        db.refresh(score_entry)
        return score_entry

    all_updates = (
        db.query(ClientUpdate)
        .filter(ClientUpdate.round_id == round_id)
        .all()
    )

    distances = [
        u.euclidean_distance for u in all_updates
        if u.euclidean_distance is not None
    ]

    if not distances:
        score_entry = TrustScore(
            client_id=client_id,
            round_id=round_id,
            score=1.0,
            deviation_avg=0.0,
            is_flagged=False,
        )
        db.add(score_entry)
        db.commit()
        db.refresh(score_entry)
        return score_entry

    mean_dist = sum(distances) / len(distances)
    variance = sum((d - mean_dist) ** 2 for d in distances) / len(distances) if len(distances) > 1 else 0.0
    std_dev = math.sqrt(variance) if variance > 0 else 0.001

    client_dist = client_update.euclidean_distance if client_update.euclidean_distance is not None else 0.0
    deviation = abs(client_dist - mean_dist) / std_dev if std_dev > 0 else 0.0

    score = max(0.0, min(1.0, 1.0 - (deviation / 5.0)))

    is_flagged = deviation > 2.0

    score_entry = TrustScore(
        client_id=client_id,
        round_id=round_id,
        score=round(score, 4),
        deviation_avg=round(deviation, 4),
        is_flagged=is_flagged,
    )
    db.add(score_entry)
    db.commit()
    db.refresh(score_entry)
    return score_entry


def get_trust_timeline(db: Session, client_id: int) -> List[TrustScore]:
    """Get the trust score history for a specific client, ordered by round."""
    return (
        db.query(TrustScore)
        .filter(TrustScore.client_id == client_id)
        .order_by(TrustScore.round_id)
        .all()
    )


def get_latest_trust_score(db: Session, client_id: int) -> Optional[TrustScore]:
    """Get the most recent trust score for a client."""
    return (
        db.query(TrustScore)
        .filter(TrustScore.client_id == client_id)
        .order_by(desc(TrustScore.computed_at))
        .first()
    )
