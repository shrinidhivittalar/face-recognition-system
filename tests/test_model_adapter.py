from pathlib import Path

import cv2
import numpy as np
import pytest

from ml.model_adapter import (
    FaceRecognitionPipeline,
    NoFaceDetectedError,
    MultipleFacesDetectedError,
)
from ml.matching import cosine_similarity

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def pipeline():
    return FaceRecognitionPipeline()


def _load(name: str) -> np.ndarray:
    image = cv2.imread(str(FIXTURES / name))
    assert image is not None, f"fixture missing: {name}"
    return image


def test_blank_image_raises_no_face(pipeline):
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    with pytest.raises(NoFaceDetectedError):
        pipeline.process(blank)


def test_two_faces_raises_multiple_faces(pipeline):
    with pytest.raises(MultipleFacesDetectedError):
        pipeline.process(_load("two_faces.jpg"))


def test_single_face_produces_normalized_embedding(pipeline):
    result = pipeline.process(_load("single_face_a1.jpg"))
    assert result.embedding.shape == (128,)
    assert np.linalg.norm(result.embedding) == pytest.approx(1.0, abs=1e-4)


def test_genuine_pair_scores_higher_than_impostor_pair(pipeline):
    a1 = pipeline.process(_load("single_face_a1.jpg")).embedding
    a2 = pipeline.process(_load("single_face_a2.jpg")).embedding
    b1 = pipeline.process(_load("single_face_b1.jpg")).embedding

    genuine_score = cosine_similarity(a1, a2)
    impostor_score = cosine_similarity(a1, b1)

    assert genuine_score > impostor_score
    assert genuine_score > 0.5
    assert impostor_score < 0.5
