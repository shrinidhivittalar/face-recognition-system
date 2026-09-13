# Evaluation Results

## Model
- Detector: YuNet (face_detection_yunet_2023mar.onnx)
- Recognizer: SFace (face_recognition_sface_2021dec.onnx)
- Similarity metric: cosine similarity on L2-normalized embeddings

## Dataset
- Source: LFW verification pairs (logasja/lfw parquet mirror, View 1 protocol)
- Calibration (train) pairs: 854 scored / 1000 total (146 excluded by the exactly-one-face policy)
- Held-out (test) pairs: 1860 scored / 2200 total (340 excluded by the exactly-one-face policy)

## Threshold Selection (calibrated on the train split)
- Method: `far_ceiling` (target FAR <= 1.00%)
- **Chosen threshold: 0.2975**
- Train FAR: 0.91%
- Train FRR: 1.45%
- Train accuracy: 98.83%

## Held-Out Test Performance (frozen threshold, unseen pairs)
- FAR: 0.86%
- FRR: 0.54%
- Accuracy: 99.30%
- Genuine pairs accepted: 924 / 929
- Impostor pairs rejected: 923 / 931

## Known Failure Cases
- 486 pairs across both splits contained images where the exactly-one-face policy rejected the image before a similarity score could even be computed. Manual inspection of a sample of exclusions showed the majority were `multiple_faces` rejections, not `no_face` rejections — LFW images are not all strictly single-subject; several contain a bystander or partially visible second person in frame, which YuNet correctly detects and the exactly-one-face policy correctly refuses to silently resolve. These are legitimate pipeline rejections, not matching errors, and are excluded from FAR/FRR.
- Remaining FAR (0.86%) and FRR (0.54%) on the held-out test split represent look-alike/false-acceptance and lighting/pose-driven false-rejection cases respectively.

## Limitations
- LFW is celebrity/public-figure photography and skews toward frontal, well-lit adult faces; real-world enrollment photos may perform worse.
- The threshold is calibrated on LFW pairs, not on this system's actual enrolled population; re-calibration is recommended if deployed against a materially different demographic or camera setup.
- No liveness detection: this evaluates recognition accuracy only, not spoof resistance.