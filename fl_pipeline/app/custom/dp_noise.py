"""
Differential Privacy via Gaussian noise injection.

This module implements the *Gaussian mechanism* for (epsilon, delta)-DP.
Before noise is added, per-parameter gradient tensors are clipped to a
bounded L2 norm so that the global sensitivity is known.

**Privacy guarantee:**

    For a function f with L2 sensitivity  Delta_f  and Gaussian noise
    with  sigma = Delta_f * sqrt(2 * ln(1.25 / delta)) / epsilon,
    the mechanism satisfies  (epsilon, delta)-DP.

After *T* rounds of composition the total privacy budget degrades.  We
provide a simple advanced-composition estimate:

    epsilon_total ~ epsilon * sqrt(2 * T * ln(1/delta)) + T * epsilon * (e^epsilon - 1)

which is tighter than naive linear composition.
"""

from __future__ import annotations

import math
from collections import OrderedDict
from typing import Dict

import torch


class DPNoise:
    """Apply differential-privacy noise to model parameter updates.

    Args:
        epsilon: Privacy budget per round.  Smaller = more private.
        delta: Probability of privacy breach (should be << 1/N).
        sensitivity: L2 sensitivity of the query (usually 1.0 after
            clipping).
        max_grad_norm: Maximum L2 norm to which each parameter tensor
            is clipped before noise injection.
    """

    def __init__(
        self,
        epsilon: float = 1.0,
        delta: float = 1e-5,
        sensitivity: float = 1.0,
        max_grad_norm: float = 1.0,
    ) -> None:
        if epsilon <= 0:
            raise ValueError(f"epsilon must be positive, got {epsilon}")
        if delta <= 0 or delta >= 1:
            raise ValueError(f"delta must be in (0, 1), got {delta}")

        self.epsilon = epsilon
        self.delta = delta
        self.sensitivity = sensitivity
        self.max_grad_norm = max_grad_norm
        self.sigma = self.compute_sigma()

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def compute_sigma(self) -> float:
        """Compute the Gaussian noise standard deviation.

        Formula:
            sigma = sensitivity * sqrt(2 * ln(1.25 / delta)) / epsilon

        Returns:
            The noise scale (standard deviation).
        """
        return self.sensitivity * math.sqrt(2.0 * math.log(1.25 / self.delta)) / self.epsilon

    def clip_gradients(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Clip each parameter tensor so its L2 norm does not exceed
        ``max_grad_norm``.

        The clipping is applied *per-tensor*: each tensor is independently
        rescaled if its norm exceeds the threshold.

        Args:
            state_dict: Mapping of parameter names to tensors.

        Returns:
            A new state dict with clipped tensors.
        """
        clipped = OrderedDict()
        for name, tensor in state_dict.items():
            norm = torch.norm(tensor.float(), p=2)
            clip_factor = min(1.0, self.max_grad_norm / (norm.item() + 1e-12))
            clipped[name] = tensor.float() * clip_factor
        return clipped

    def add_noise(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Add Gaussian noise  N(0, sigma^2)  to every parameter tensor.

        Args:
            state_dict: Mapping of parameter names to tensors.

        Returns:
            A new state dict with noise added.
        """
        noised = OrderedDict()
        for name, tensor in state_dict.items():
            noise = torch.randn_like(tensor.float()) * self.sigma
            noised[name] = tensor.float() + noise
        return noised

    def apply(self, state_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """Clip gradients and then add calibrated Gaussian noise.

        This is the standard Gaussian mechanism pipeline:
        1. Clip each tensor to ``max_grad_norm``.
        2. Add  N(0, sigma^2)  noise.

        Args:
            state_dict: Mapping of parameter names to tensors.

        Returns:
            A new state dict that satisfies (epsilon, delta)-DP for this
            round.
        """
        clipped = self.clip_gradients(state_dict)
        return self.add_noise(clipped)

    # ------------------------------------------------------------------
    # Privacy accounting
    # ------------------------------------------------------------------

    def get_privacy_spent(self, num_rounds: int) -> Dict[str, float]:
        """Estimate cumulative privacy loss after *num_rounds* of composition.

        Uses the *advanced composition theorem* (Dwork, Rothblum, Vadhan 2010):

            epsilon_total <= epsilon * sqrt(2 * T * ln(1/delta')) + T * epsilon * (e^epsilon - 1)
            delta_total   <= T * delta + delta'

        where we set  delta' = delta  for simplicity.

        Args:
            num_rounds: Number of DP-mechanism invocations (FL rounds).

        Returns:
            A dict with keys ``epsilon_total``, ``delta_total``, and
            ``num_rounds``.
        """
        T = num_rounds
        eps = self.epsilon
        delta_prime = self.delta

        # Advanced composition bound
        eps_total = eps * math.sqrt(2.0 * T * math.log(1.0 / delta_prime)) + T * eps * (math.exp(eps) - 1.0)
        delta_total = T * self.delta + delta_prime

        return {
            "epsilon_total": round(eps_total, 6),
            "delta_total": round(delta_total, 10),
            "num_rounds": T,
            "sigma": round(self.sigma, 6),
        }
