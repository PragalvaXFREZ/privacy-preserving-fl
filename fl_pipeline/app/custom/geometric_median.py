"""
Geometric Median aggregation via Weiszfeld's iterative algorithm.

In Federated Learning the geometric median is a *robust* aggregation
strategy: unlike the arithmetic mean it is resilient to Byzantine
(adversarial or faulty) client updates because a single outlier cannot
pull the aggregate arbitrarily far from the bulk of honest clients.

**Algorithm (Weiszfeld, 1937)**

Given *n* points  x_1, ..., x_n  in  R^d  the geometric median is:

    argmin_y  SUM_i || y - x_i ||_2

Weiszfeld's iterative scheme:

    y^{t+1} = ( SUM_i  w_i^t  x_i ) / ( SUM_i  w_i^t )

where  w_i^t = 1 / || y^t - x_i ||_2  .

The iteration converges to the geometric median when no iterate
coincides with one of the input points.  We handle the degenerate case
(distance == 0) by clamping the weight to a large finite value.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Dict, List, Tuple

import numpy as np
import torch


class GeometricMedianAggregator:
    """Compute the geometric median of a set of model state dicts.

    Args:
        max_iter: Maximum number of Weiszfeld iterations.
        eps: Convergence threshold -- stop when the update moves less
            than *eps* in L2 norm.
    """

    def __init__(self, max_iter: int = 100, eps: float = 1e-5) -> None:
        self.max_iter = max_iter
        self.eps = eps

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def aggregate(self, client_updates: List[Dict[str, torch.Tensor]]) -> Dict[str, torch.Tensor]:
        """Aggregate a list of client state dicts using the geometric median.

        Each element of *client_updates* is a state dict mapping
        parameter names to tensors (all must share the same keys and
        shapes).

        The algorithm:

        1. Flatten every client's parameters into a single 1-D vector.
        2. Run Weiszfeld on the resulting ``(num_clients, D)`` matrix.
        3. Reshape the median vector back into the original parameter
           shapes and return as a new state dict.

        Args:
            client_updates: A list of state dicts, one per client.

        Returns:
            An aggregated state dict representing the geometric median.
        """
        if not client_updates:
            raise ValueError("client_updates must be a non-empty list")

        if len(client_updates) == 1:
            # Trivial case -- single client, just return a copy
            return OrderedDict(
                (k, v.clone()) for k, v in client_updates[0].items()
            )

        # Collect the ordered keys and their shapes for reconstruction
        param_keys: List[str] = list(client_updates[0].keys())
        param_shapes: List[torch.Size] = [
            client_updates[0][k].shape for k in param_keys
        ]
        param_numels: List[int] = [
            client_updates[0][k].numel() for k in param_keys
        ]

        # Flatten each client's parameters into a single numpy vector
        points = np.stack(
            [
                self._flatten_state_dict(sd, param_keys)
                for sd in client_updates
            ],
            axis=0,
        )  # shape: (num_clients, D)

        # Run Weiszfeld
        median_flat, _num_iters = self._weiszfeld(points)

        # Reconstruct the state dict from the flat median vector
        aggregated = self._unflatten_to_state_dict(
            median_flat, param_keys, param_shapes, param_numels
        )
        return aggregated

    def compute_distances(
        self,
        client_updates: List[Dict[str, torch.Tensor]],
        median: Dict[str, torch.Tensor],
    ) -> List[float]:
        """Compute the Euclidean distance of each client update from *median*.

        This is useful for computing trust scores -- clients whose
        updates are far from the geometric median are potential
        Byzantine actors.

        Args:
            client_updates: List of client state dicts.
            median: The aggregated (geometric median) state dict.

        Returns:
            A list of scalar distances, one per client.
        """
        param_keys = list(median.keys())
        median_flat = self._flatten_state_dict(median, param_keys)

        distances: List[float] = []
        for sd in client_updates:
            client_flat = self._flatten_state_dict(sd, param_keys)
            dist = float(np.linalg.norm(client_flat - median_flat))
            distances.append(dist)
        return distances

    # ------------------------------------------------------------------
    # Weiszfeld core
    # ------------------------------------------------------------------

    def _weiszfeld(self, points: np.ndarray) -> Tuple[np.ndarray, int]:
        """Run Weiszfeld's iterative algorithm on a set of points.

        Args:
            points: Array of shape ``(num_clients, D)`` where each row
                is a flattened parameter vector.

        Returns:
            A tuple ``(median_vector, num_iterations)`` where
            *median_vector* has shape ``(D,)`` and *num_iterations* is
            the number of iterations actually performed.
        """
        # Initialise the estimate as the componentwise mean
        y = np.mean(points, axis=0)

        for iteration in range(1, self.max_iter + 1):
            # Compute distances from the current estimate to each point
            diffs = points - y[np.newaxis, :]  # (n, D)
            distances = np.linalg.norm(diffs, axis=1)  # (n,)

            # Compute weights = 1 / distance, handling zero distances
            # If a point coincides with the current estimate, assign a
            # very large but finite weight (effectively snapping to it).
            weights = np.where(
                distances > 1e-12,
                1.0 / distances,
                1e12,
            )  # (n,)

            # Weighted average
            total_weight = np.sum(weights)
            y_new = np.sum(
                weights[:, np.newaxis] * points, axis=0
            ) / total_weight

            # Check convergence
            shift = np.linalg.norm(y_new - y)
            y = y_new

            if shift < self.eps:
                return y, iteration

        return y, self.max_iter

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_state_dict(
        state_dict: Dict[str, torch.Tensor],
        keys: List[str],
    ) -> np.ndarray:
        """Flatten a state dict's tensors into a single 1-D numpy array."""
        parts = [
            state_dict[k].detach().cpu().float().numpy().ravel()
            for k in keys
        ]
        return np.concatenate(parts)

    @staticmethod
    def _unflatten_to_state_dict(
        flat: np.ndarray,
        keys: List[str],
        shapes: List[torch.Size],
        numels: List[int],
    ) -> OrderedDict:
        """Reconstruct a state dict from a flat numpy array."""
        result = OrderedDict()
        offset = 0
        for key, shape, numel in zip(keys, shapes, numels):
            arr = flat[offset : offset + numel].copy()
            result[key] = torch.tensor(arr, dtype=torch.float32).reshape(shape)
            offset += numel
        return result
