"""
Tests for the Geometric Median aggregator (Weiszfeld's algorithm).

Covers:
- Known geometric median of simple 2-D points.
- Byzantine outlier resilience.
- Degenerate case where all points are identical.
- Aggregation of state-dict-style tensors (layer weights/biases).
"""

import numpy as np
import pytest
import torch

from fl_pipeline.app.custom.geometric_median import GeometricMedianAggregator


class TestWeiszfeldKnownMedian:
    """The geometric median of (0,0), (1,0), (0,1) is approximately
    (0.3113, 0.3113) -- the point that minimises the sum of Euclidean
    distances to all three vertices.
    """

    def test_known_median(self):
        agg = GeometricMedianAggregator(max_iter=200, eps=1e-8)

        # Represent the three 2-D points as single-key state dicts
        updates = [
            {"point": torch.tensor([0.0, 0.0])},
            {"point": torch.tensor([1.0, 0.0])},
            {"point": torch.tensor([0.0, 1.0])},
        ]

        result = agg.aggregate(updates)
        median = result["point"].numpy()

        # The analytic geometric median of these three points is
        # approximately (0.3113, 0.3113).
        np.testing.assert_allclose(median, [0.3113, 0.3113], atol=0.01)


class TestByzantineOutlier:
    """An extreme outlier at (1000, 1000) should have a much larger
    Euclidean distance from the geometric median than the honest clients.
    """

    def test_byzantine_outlier(self):
        agg = GeometricMedianAggregator(max_iter=200, eps=1e-8)

        updates = [
            {"point": torch.tensor([0.0, 0.0])},
            {"point": torch.tensor([1.0, 0.0])},
            {"point": torch.tensor([0.0, 1.0])},
            {"point": torch.tensor([1000.0, 1000.0])},  # Byzantine
        ]

        median = agg.aggregate(updates)
        distances = agg.compute_distances(updates, median)

        # The outlier (index 3) should be far from the median
        honest_max = max(distances[:3])
        outlier_dist = distances[3]

        assert outlier_dist > 10 * honest_max, (
            f"Outlier distance ({outlier_dist:.2f}) should be much larger "
            f"than honest max ({honest_max:.2f})"
        )


class TestIdenticalPoints:
    """When all input points are identical, the geometric median should
    be that same point, and the algorithm should converge quickly.
    """

    def test_identical_points(self):
        agg = GeometricMedianAggregator(max_iter=100, eps=1e-6)

        point = torch.tensor([3.14, 2.72, 1.41])
        updates = [{"vec": point.clone()} for _ in range(5)]

        result = agg.aggregate(updates)
        np.testing.assert_allclose(
            result["vec"].numpy(), point.numpy(), atol=1e-4
        )

        # All distances should be essentially zero
        distances = agg.compute_distances(updates, result)
        for d in distances:
            assert d < 1e-3, f"Distance should be ~0, got {d}"


class TestStateDictAggregation:
    """Aggregate three fake state dicts with multiple parameter tensors
    and verify the output preserves keys and shapes.
    """

    def test_state_dict_aggregation(self):
        agg = GeometricMedianAggregator()

        torch.manual_seed(0)
        updates = []
        for _ in range(3):
            sd = {
                "layer1.weight": torch.randn(16, 8),
                "layer2.bias": torch.randn(16),
            }
            updates.append(sd)

        result = agg.aggregate(updates)

        # Same keys
        assert set(result.keys()) == {"layer1.weight", "layer2.bias"}

        # Same shapes
        assert result["layer1.weight"].shape == torch.Size([16, 8])
        assert result["layer2.bias"].shape == torch.Size([16])

        # Distances should all be finite and non-negative
        distances = agg.compute_distances(updates, result)
        assert len(distances) == 3
        for d in distances:
            assert d >= 0.0
            assert np.isfinite(d)
