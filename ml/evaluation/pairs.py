"""Runs the detection+embedding pipeline over pairs and records similarity scores.

Pairs whose images fail the exactly-one-face policy (no face / multiple faces)
are excluded from the similarity distributions and recorded as explicit
evaluation failure cases (blueprint section 8 / PRD section 17), rather than
silently dropped.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ml.evaluation.dataset import ImagePair
from ml.matching import cosine_similarity
from ml.model_adapter import (
    FaceRecognitionPipeline,
    MultipleFacesDetectedError,
    NoFaceDetectedError,
)


@dataclass
class ScoredPair:
    path_0: str
    path_1: str
    is_genuine: bool
    score: float


@dataclass
class PairEvaluationResult:
    scored_pairs: list[ScoredPair] = field(default_factory=list)
    failed_pairs: list[dict] = field(default_factory=list)


def score_pairs(
    pipeline: FaceRecognitionPipeline,
    image_pairs: list[ImagePair],
    embedding_cache: dict | None = None,
) -> PairEvaluationResult:
    """Compute cosine similarity for each pair, caching embeddings by image path."""
    if embedding_cache is None:
        embedding_cache = {}

    result = PairEvaluationResult()

    def get_embedding(path: str, image):
        if path in embedding_cache:
            return embedding_cache[path]
        try:
            processed = pipeline.process(image)
            embedding_cache[path] = ("ok", processed.embedding)
        except NoFaceDetectedError:
            embedding_cache[path] = ("no_face", None)
        except MultipleFacesDetectedError:
            embedding_cache[path] = ("multiple_faces", None)
        return embedding_cache[path]

    for pair in image_pairs:
        status_0, embedding_0 = get_embedding(pair.path_0, pair.image_0)
        status_1, embedding_1 = get_embedding(pair.path_1, pair.image_1)

        if status_0 != "ok" or status_1 != "ok":
            result.failed_pairs.append(
                {
                    "path_0": pair.path_0,
                    "path_1": pair.path_1,
                    "is_genuine": pair.is_genuine,
                    "reason_0": status_0,
                    "reason_1": status_1,
                }
            )
            continue

        score = cosine_similarity(embedding_0, embedding_1)
        result.scored_pairs.append(
            ScoredPair(
                path_0=pair.path_0,
                path_1=pair.path_1,
                is_genuine=pair.is_genuine,
                score=score,
            )
        )

    return result
