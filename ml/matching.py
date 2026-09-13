"""Cosine similarity matching and identity aggregation (ADR-003)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two vectors. Assumes callers may pass unnormalized vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


@dataclass
class MatchResult:
    identity_id: str | None
    score: float
    outcome: str  # "known" or "unknown"


def best_match(
    query_embedding: np.ndarray,
    enrolled_embeddings: list[tuple[str, np.ndarray]],
    threshold: float,
) -> MatchResult:
    """Compare a query embedding against enrolled (identity_id, embedding) samples.

    Aggregation rule: an identity's score is the MAX similarity across all of its
    stored samples (best-sample-wins). This rewards a single strong match while
    tolerating enrollment samples of varying quality. See docs/ADR for rationale.
    """
    if not enrolled_embeddings:
        return MatchResult(identity_id=None, score=0.0, outcome="unknown")

    best_identity_id = None
    best_score = -1.0
    for identity_id, embedding in enrolled_embeddings:
        score = cosine_similarity(query_embedding, embedding)
        if score > best_score:
            best_score = score
            best_identity_id = identity_id

    if best_score >= threshold:
        return MatchResult(identity_id=best_identity_id, score=best_score, outcome="known")
    return MatchResult(identity_id=None, score=best_score, outcome="unknown")
