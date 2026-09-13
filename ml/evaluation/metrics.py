"""FAR/FRR and related verification metrics for a set of scored pairs."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ml.evaluation.pairs import ScoredPair


@dataclass
class ThresholdMetrics:
    threshold: float
    far: float  # False Acceptance Rate: impostor pairs incorrectly accepted
    frr: float  # False Rejection Rate: genuine pairs incorrectly rejected
    accuracy: float
    genuine_accepted: int
    genuine_total: int
    impostor_rejected: int
    impostor_total: int


def compute_metrics_at_threshold(scored_pairs: list[ScoredPair], threshold: float) -> ThresholdMetrics:
    genuine = [p for p in scored_pairs if p.is_genuine]
    impostor = [p for p in scored_pairs if not p.is_genuine]

    genuine_accepted = sum(1 for p in genuine if p.score >= threshold)
    impostor_accepted = sum(1 for p in impostor if p.score >= threshold)
    impostor_rejected = len(impostor) - impostor_accepted
    genuine_rejected = len(genuine) - genuine_accepted

    frr = genuine_rejected / len(genuine) if genuine else 0.0
    far = impostor_accepted / len(impostor) if impostor else 0.0
    correct = genuine_accepted + impostor_rejected
    accuracy = correct / len(scored_pairs) if scored_pairs else 0.0

    return ThresholdMetrics(
        threshold=threshold,
        far=far,
        frr=frr,
        accuracy=accuracy,
        genuine_accepted=genuine_accepted,
        genuine_total=len(genuine),
        impostor_rejected=impostor_rejected,
        impostor_total=len(impostor),
    )


def sweep_thresholds(scored_pairs: list[ScoredPair], num_steps: int = 200) -> list[ThresholdMetrics]:
    """Evaluate FAR/FRR across a grid of thresholds spanning the observed score range."""
    scores = np.array([p.score for p in scored_pairs])
    lo, hi = float(scores.min()), float(scores.max())
    thresholds = np.linspace(lo, hi, num_steps)
    return [compute_metrics_at_threshold(scored_pairs, float(t)) for t in thresholds]
