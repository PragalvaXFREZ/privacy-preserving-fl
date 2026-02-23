"""
NVFlare Server Controller using Geometric Median aggregation.

This controller orchestrates the federated learning rounds:
1. Broadcasts the current global model to all clients.
2. Collects client updates (body in plaintext with DP noise,
   head encrypted via CKKS).
3. Aggregates body weights using the geometric median (robust
   against Byzantine clients).
4. Averages head weights (simple mean for encrypted weights).
5. Writes per-round metrics and trust scores to the database.
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Optional

from nvflare.apis.controller_spec import Controller, Task, ClientTask
from nvflare.apis.fl_context import FLContext
from nvflare.apis.signal import Signal
from nvflare.apis.shareable import Shareable, make_reply
from nvflare.apis.fl_constant import ReturnCode, FLContextKey
from nvflare.app_common.abstract.model import make_model_learnable, model_learnable_to_dict

from .geometric_median import GeometricMedianAggregator
from .db_writer import DBWriter

logger = logging.getLogger(__name__)


class GeomMedianController(Controller):
    """Server-side controller that aggregates client updates via geometric median.

    Args:
        num_rounds: Total number of federated learning rounds.
        min_clients: Minimum number of client responses required per round.
        db_url: PostgreSQL connection string for metrics logging.
    """

    def __init__(self, num_rounds=20, min_clients=3, db_url=None):
        super().__init__()
        self.num_rounds = num_rounds
        self.min_clients = min_clients
        self.aggregator = GeometricMedianAggregator()
        self.db_writer = DBWriter(db_url) if db_url else None
        self.global_model_weights = None

    def start_controller(self, fl_ctx: FLContext):
        logger.info("GeomMedianController starting")

    def stop_controller(self, fl_ctx: FLContext):
        if self.db_writer:
            self.db_writer.close()
        logger.info("GeomMedianController stopped")

    def control_flow(self, abort_signal: Signal, fl_ctx: FLContext):
        for round_num in range(1, self.num_rounds + 1):
            if abort_signal.triggered:
                break

            logger.info(f"Starting round {round_num}/{self.num_rounds}")
            round_start = datetime.utcnow()

            # Report round start to DB
            round_db_id = None
            if self.db_writer:
                round_db_id = self.db_writer.write_round(
                    round_number=round_num,
                    job_id=fl_ctx.get_job_id() if hasattr(fl_ctx, 'get_job_id') else None,
                    status="in_progress",
                    num_clients=self.min_clients,
                    started_at=round_start,
                )

            # Create train task and broadcast
            task = Task(name="train", data=Shareable())
            if self.global_model_weights:
                task.data["weights"] = self.global_model_weights
            task.data["round_number"] = round_num

            self.broadcast_and_wait(
                task=task,
                targets=None,  # all clients
                min_responses=self.min_clients,
                fl_ctx=fl_ctx,
                abort_signal=abort_signal,
            )

            # Collect results
            client_results = []
            for client_task in task.client_tasks:
                result = client_task.result
                if result and result.get_return_code() == ReturnCode.OK:
                    client_results.append({
                        "client_name": client_task.client.name,
                        "body_weights": result.get("body_weights", {}),
                        "head_weights": result.get("head_weights", {}),
                        "meta": {
                            "local_loss": result.get("local_loss", 0.0),
                            "local_auc": result.get("local_auc", 0.0),
                            "num_samples": result.get("num_samples", 0),
                            "encryption_status": result.get("encryption_status", "plaintext"),
                        },
                    })

            if len(client_results) < self.min_clients:
                logger.warning(f"Round {round_num}: only {len(client_results)} responses, need {self.min_clients}")
                if self.db_writer and round_db_id:
                    self.db_writer.write_round(round_num, None, "failed", len(client_results))
                continue

            # Aggregate body weights using geometric median
            agg_start = time.time()
            body_updates = [r["body_weights"] for r in client_results]
            aggregated_body = self.aggregator.aggregate(body_updates)
            distances = self.aggregator.compute_distances(body_updates, aggregated_body)
            agg_time_ms = int((time.time() - agg_start) * 1000)

            # Aggregate head weights (simple averaging for encrypted weights)
            head_updates = [r["head_weights"] for r in client_results]
            aggregated_head = {}
            if head_updates and head_updates[0]:
                for key in head_updates[0]:
                    stacked = [h[key] for h in head_updates if key in h]
                    if stacked:
                        import torch
                        aggregated_head[key] = torch.stack(stacked).mean(dim=0)

            # Update global model
            self.global_model_weights = {**aggregated_body, **aggregated_head}

            # Compute global metrics (average of client metrics)
            avg_loss = sum(r["meta"]["local_loss"] for r in client_results) / len(client_results)
            avg_auc = sum(r["meta"]["local_auc"] for r in client_results) / len(client_results)

            round_end = datetime.utcnow()

            # Write metrics to DB
            if self.db_writer and round_db_id:
                self.db_writer.write_round(
                    round_number=round_num, job_id=None, status="completed",
                    num_clients=len(client_results),
                    global_loss=avg_loss, global_auc=avg_auc,
                    started_at=round_start, completed_at=round_end,
                )

                weiszfeld_iters = getattr(self.aggregator, '_last_iterations', 0)
                self.db_writer.write_round_metric(
                    round_id=round_db_id,
                    aggregation_method="geometric_median",
                    weiszfeld_iterations=weiszfeld_iters,
                    convergence_epsilon=self.aggregator.eps,
                    encryption_overhead_ms=0,
                    aggregation_time_ms=agg_time_ms,
                    poisoned_clients_detected=sum(1 for d in distances if d > 2.0),
                )

                for i, cr in enumerate(client_results):
                    dist = distances[i] if i < len(distances) else 0.0
                    trust = 1.0 / (1.0 + dist)
                    self.db_writer.write_client_update(
                        round_id=round_db_id,
                        client_name=cr["client_name"],
                        local_loss=cr["meta"]["local_loss"],
                        local_auc=cr["meta"]["local_auc"],
                        num_samples=cr["meta"]["num_samples"],
                        euclidean_distance=dist,
                        encryption_status=cr["meta"]["encryption_status"],
                    )
                    self.db_writer.write_trust_score(
                        client_name=cr["client_name"],
                        round_id=round_db_id,
                        score=trust,
                        deviation_avg=dist,
                        is_flagged=(trust < 0.3),
                    )

            logger.info(f"Round {round_num} completed: loss={avg_loss:.4f}, auc={avg_auc:.4f}")

    def process_result_of_unknown_task(self, client, task_name, client_task_id, result, fl_ctx):
        logger.warning(f"Unknown task result from {client.name}: {task_name}")
