import numpy as np
import pytest

from ml.matching import cosine_similarity, best_match, MatchResult


def test_cosine_similarity_identical_vectors():
    v = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(v, v) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal_vectors():
    a = np.array([1.0, 0.0])
    b = np.array([0.0, 1.0])
    assert cosine_similarity(a, b) == pytest.approx(0.0)


def test_cosine_similarity_opposite_vectors():
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    assert cosine_similarity(a, b) == pytest.approx(-1.0)


def test_cosine_similarity_zero_vector_is_safe():
    a = np.zeros(3)
    b = np.array([1.0, 2.0, 3.0])
    assert cosine_similarity(a, b) == 0.0


def test_best_match_returns_unknown_when_no_enrollments():
    query = np.array([1.0, 0.0])
    result = best_match(query, [], threshold=0.5)
    assert result.outcome == "unknown"
    assert result.identity_id is None


def test_best_match_accepts_above_threshold():
    query = np.array([1.0, 0.0])
    enrolled = [("alice", np.array([1.0, 0.0])), ("bob", np.array([0.0, 1.0]))]
    result = best_match(query, enrolled, threshold=0.9)
    assert result.outcome == "known"
    assert result.identity_id == "alice"
    assert result.score == pytest.approx(1.0)


def test_best_match_rejects_below_threshold_without_leaking_candidate():
    query = np.array([0.6, 0.4])
    enrolled = [("alice", np.array([1.0, 0.0]))]
    result = best_match(query, enrolled, threshold=0.99)
    assert result.outcome == "unknown"
    assert result.identity_id is None


def test_best_match_picks_max_across_multiple_samples_same_identity():
    query = np.array([1.0, 0.0])
    enrolled = [
        ("alice", np.array([0.0, 1.0])),  # poor sample
        ("alice", np.array([1.0, 0.01])),  # good sample, should win
    ]
    result = best_match(query, enrolled, threshold=0.5)
    assert result.outcome == "known"
    assert result.identity_id == "alice"
