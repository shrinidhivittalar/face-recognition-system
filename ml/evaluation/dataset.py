"""Loads the LFW genuine/impostor pairs dataset used for threshold calibration.

Source: logasja/lfw on Hugging Face (parquet mirror of the standard LFW "View 1"
pairsDevTrain/pairsDevTest verification protocol). Pair label 1 = genuine
(same identity), 0 = impostor (different identities), confirmed against the
embedded image filenames (e.g. Aaron_Peirsol_0001.jpg / Aaron_Peirsol_0002.jpg).

LFW is distributed for non-commercial research/benchmarking use; it is used
here only to calibrate and evaluate the matching threshold, not redistributed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import cv2

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"
TRAIN_PAIRS_PATH = DATA_DIR / "lfw_pairs_train.parquet"
TEST_PAIRS_PATH = DATA_DIR / "lfw_pairs_test.parquet"


@dataclass
class ImagePair:
    path_0: str
    path_1: str
    image_0: np.ndarray
    image_1: np.ndarray
    is_genuine: bool  # True if same identity


def _decode(image_struct: dict) -> np.ndarray:
    buffer = np.frombuffer(image_struct["bytes"], dtype=np.uint8)
    return cv2.imdecode(buffer, cv2.IMREAD_COLOR)


def load_pairs(parquet_path: Path) -> list[ImagePair]:
    """Load an LFW pairs parquet file into decoded BGR image pairs."""
    table = pq.read_table(parquet_path)
    rows = table.to_pylist()
    pairs = []
    for row in rows:
        pairs.append(
            ImagePair(
                path_0=row["img_0"]["path"],
                path_1=row["img_1"]["path"],
                image_0=_decode(row["img_0"]),
                image_1=_decode(row["img_1"]),
                is_genuine=bool(row["pair"] == 1),
            )
        )
    return pairs


def load_train_pairs() -> list[ImagePair]:
    return load_pairs(TRAIN_PAIRS_PATH)


def load_test_pairs() -> list[ImagePair]:
    return load_pairs(TEST_PAIRS_PATH)
