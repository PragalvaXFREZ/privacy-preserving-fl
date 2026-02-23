"""
Database writer for Federated Learning metrics.

Connects to PostgreSQL and writes per-round training metrics, client
updates, aggregation statistics, and trust scores.  Uses lightweight
SQLAlchemy Core table mirrors (not full ORM models) to stay decoupled
from the dashboard's own model definitions.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    Float,
    String,
    Boolean,
    DateTime,
    Text,
    select,
    update,
    insert,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DBWriter:
    """Write FL pipeline metrics into PostgreSQL.

    Args:
        db_url: SQLAlchemy connection string, e.g.
            ``"postgresql://user:pass@host:5432/dbname"``.
    """

    def __init__(self, db_url: str) -> None:
        self.engine = create_engine(db_url, pool_pre_ping=True, pool_size=5)
        self.metadata = MetaData()
        self._reflect_tables()

    # ------------------------------------------------------------------
    # Table reflection
    # ------------------------------------------------------------------

    def _reflect_tables(self) -> None:
        """Reflect (mirror) the tables we need from the existing schema.

        If a table does not yet exist in the database we define a
        lightweight stand-in so that writes degrade gracefully.
        """
        try:
            self.metadata.reflect(bind=self.engine)
        except Exception as exc:
            logger.warning(f"Could not reflect database schema: {exc}")

        # training_rounds
        if "training_rounds" in self.metadata.tables:
            self.training_rounds = self.metadata.tables["training_rounds"]
        else:
            self.training_rounds = Table(
                "training_rounds",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("round_number", Integer, nullable=False),
                Column("job_id", String(255)),
                Column("status", String(50)),
                Column("num_clients", Integer),
                Column("global_loss", Float),
                Column("global_auc", Float),
                Column("started_at", DateTime),
                Column("completed_at", DateTime),
                extend_existing=True,
            )

        # client_updates
        if "client_updates" in self.metadata.tables:
            self.client_updates = self.metadata.tables["client_updates"]
        else:
            self.client_updates = Table(
                "client_updates",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("round_id", Integer),
                Column("client_id", Integer),
                Column("local_loss", Float),
                Column("local_auc", Float),
                Column("num_samples", Integer),
                Column("euclidean_distance", Float),
                Column("encryption_status", String(50)),
                Column("submitted_at", DateTime),
                extend_existing=True,
            )

        # round_metrics
        if "round_metrics" in self.metadata.tables:
            self.round_metrics = self.metadata.tables["round_metrics"]
        else:
            self.round_metrics = Table(
                "round_metrics",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("round_id", Integer),
                Column("aggregation_method", String(100)),
                Column("weiszfeld_iterations", Integer),
                Column("convergence_epsilon", Float),
                Column("encryption_overhead_ms", Integer),
                Column("aggregation_time_ms", Integer),
                Column("poisoned_clients_detected", Integer),
                extend_existing=True,
            )

        # trust_scores
        if "trust_scores" in self.metadata.tables:
            self.trust_scores = self.metadata.tables["trust_scores"]
        else:
            self.trust_scores = Table(
                "trust_scores",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("client_id", Integer),
                Column("round_id", Integer),
                Column("score", Float),
                Column("deviation_avg", Float),
                Column("is_flagged", Boolean),
                Column("created_at", DateTime),
                extend_existing=True,
            )

        # clients
        if "clients" in self.metadata.tables:
            self.clients = self.metadata.tables["clients"]
        else:
            self.clients = Table(
                "clients",
                self.metadata,
                Column("id", Integer, primary_key=True, autoincrement=True),
                Column("client_id", String(255)),
                Column("name", String(255)),
                Column("status", String(50)),
                Column("last_heartbeat", DateTime),
                extend_existing=True,
            )

    # ------------------------------------------------------------------
    # Helper: look up a client by name
    # ------------------------------------------------------------------

    def _get_client_id_by_name(self, session: Session, client_name: str) -> Optional[int]:
        """Return the primary-key ``id`` for the client with *client_name*.

        Returns ``None`` if not found.
        """
        try:
            row = session.execute(
                select(self.clients.c.id).where(self.clients.c.name == client_name)
            ).first()
            return row[0] if row else None
        except Exception as exc:
            logger.warning(f"Failed to look up client '{client_name}': {exc}")
            return None

    # ------------------------------------------------------------------
    # Public write methods
    # ------------------------------------------------------------------

    def write_round(
        self,
        round_number: int,
        job_id: Optional[str],
        status: str,
        num_clients: int,
        global_loss: Optional[float] = None,
        global_auc: Optional[float] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> Optional[int]:
        """Insert or update a training round row.

        If a row with the given *round_number* already exists, it is
        updated (UPSERT behaviour).  Otherwise a new row is inserted.

        Returns:
            The primary-key ``id`` of the upserted row, or ``None`` on
            failure.
        """
        session = Session(self.engine)
        try:
            # Check whether this round already exists
            existing = session.execute(
                select(self.training_rounds.c.id).where(
                    self.training_rounds.c.round_number == round_number
                )
            ).first()

            values = {
                "round_number": round_number,
                "status": status,
                "num_clients": num_clients,
            }
            if job_id is not None:
                values["job_id"] = job_id
            if global_loss is not None:
                values["global_loss"] = global_loss
            if global_auc is not None:
                values["global_auc"] = global_auc
            if started_at is not None:
                values["started_at"] = started_at
            if completed_at is not None:
                values["completed_at"] = completed_at

            if existing:
                # Update
                session.execute(
                    update(self.training_rounds)
                    .where(self.training_rounds.c.id == existing[0])
                    .values(**values)
                )
                session.commit()
                return existing[0]
            else:
                # Insert
                result = session.execute(
                    insert(self.training_rounds).values(**values)
                )
                session.commit()
                return result.inserted_primary_key[0]
        except Exception as exc:
            session.rollback()
            logger.error(f"write_round failed: {exc}", exc_info=True)
            return None
        finally:
            session.close()

    def write_client_update(
        self,
        round_id: int,
        client_name: str,
        local_loss: float,
        local_auc: float,
        num_samples: int,
        euclidean_distance: float,
        encryption_status: str,
    ) -> Optional[int]:
        """Record a single client's contribution for a round.

        The *client_name* is resolved to a ``client.id`` via the
        ``clients`` table.

        Returns:
            The inserted row's ``id``, or ``None`` on failure.
        """
        session = Session(self.engine)
        try:
            client_pk = self._get_client_id_by_name(session, client_name)

            result = session.execute(
                insert(self.client_updates).values(
                    round_id=round_id,
                    client_id=client_pk,
                    local_loss=local_loss,
                    local_auc=local_auc,
                    num_samples=num_samples,
                    euclidean_distance=euclidean_distance,
                    encryption_status=encryption_status,
                    submitted_at=datetime.utcnow(),
                )
            )
            session.commit()
            return result.inserted_primary_key[0]
        except Exception as exc:
            session.rollback()
            logger.error(f"write_client_update failed: {exc}", exc_info=True)
            return None
        finally:
            session.close()

    def write_round_metric(
        self,
        round_id: int,
        aggregation_method: str,
        weiszfeld_iterations: int,
        convergence_epsilon: float,
        encryption_overhead_ms: int,
        aggregation_time_ms: int,
        poisoned_clients_detected: int = 0,
    ) -> Optional[int]:
        """Write aggregation-level metrics for a round.

        Returns:
            The inserted row's ``id``, or ``None`` on failure.
        """
        session = Session(self.engine)
        try:
            result = session.execute(
                insert(self.round_metrics).values(
                    round_id=round_id,
                    aggregation_method=aggregation_method,
                    weiszfeld_iterations=weiszfeld_iterations,
                    convergence_epsilon=convergence_epsilon,
                    encryption_overhead_ms=encryption_overhead_ms,
                    aggregation_time_ms=aggregation_time_ms,
                    poisoned_clients_detected=poisoned_clients_detected,
                )
            )
            session.commit()
            return result.inserted_primary_key[0]
        except Exception as exc:
            session.rollback()
            logger.error(f"write_round_metric failed: {exc}", exc_info=True)
            return None
        finally:
            session.close()

    def write_trust_score(
        self,
        client_name: str,
        round_id: int,
        score: float,
        deviation_avg: float,
        is_flagged: bool,
    ) -> Optional[int]:
        """Write a trust score for a client in a given round.

        Returns:
            The inserted row's ``id``, or ``None`` on failure.
        """
        session = Session(self.engine)
        try:
            client_pk = self._get_client_id_by_name(session, client_name)

            result = session.execute(
                insert(self.trust_scores).values(
                    client_id=client_pk,
                    round_id=round_id,
                    score=score,
                    deviation_avg=deviation_avg,
                    is_flagged=is_flagged,
                    created_at=datetime.utcnow(),
                )
            )
            session.commit()
            return result.inserted_primary_key[0]
        except Exception as exc:
            session.rollback()
            logger.error(f"write_trust_score failed: {exc}", exc_info=True)
            return None
        finally:
            session.close()

    def update_client_heartbeat(
        self,
        client_id_str: str,
        status: str = "online",
    ) -> None:
        """Update the heartbeat timestamp and status for a client.

        The client is located by its ``client_id`` column (a string
        identifier), not the integer primary key.

        Args:
            client_id_str: The string ``client_id`` value from the
                ``clients`` table.
            status: New status string (e.g. ``"online"``, ``"offline"``).
        """
        session = Session(self.engine)
        try:
            session.execute(
                update(self.clients)
                .where(self.clients.c.client_id == client_id_str)
                .values(
                    last_heartbeat=datetime.utcnow(),
                    status=status,
                )
            )
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.error(f"update_client_heartbeat failed: {exc}", exc_info=True)
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def close(self) -> None:
        """Dispose of the SQLAlchemy engine and release all connections."""
        try:
            self.engine.dispose()
            logger.info("DBWriter engine disposed")
        except Exception as exc:
            logger.warning(f"Error disposing engine: {exc}")
