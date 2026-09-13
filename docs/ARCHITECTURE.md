# Architecture

## Logical flow

```
React UI  -->  FastAPI  -->  Recognition Service  -->  Repository  -->  PostgreSQL
                                    |
                            YuNet + SFace (ONNX, via OpenCV)
```

The ML model is isolated behind `ml/model_adapter.py` (`FaceRecognitionPipeline`) so
detection/embedding could be swapped without touching the API or UI. Persistence is
isolated behind `backend/app/repositories/identity_repository.py` so PostgreSQL could
be swapped without touching services/routes.

## Layers

| Layer | Technology | Location |
|---|---|---|
| Frontend | React + TypeScript (Vite) | `frontend/` |
| Backend API | Python + FastAPI | `backend/app/api` |
| Services | Business logic (enroll/identify orchestration) | `backend/app/services` |
| Repositories | Persistence boundary | `backend/app/repositories` |
| ORM models | SQLAlchemy | `backend/app/models` |
| ML | OpenCV + YuNet + SFace | `ml/` |
| Evaluation | Threshold calibration harness | `ml/evaluation/` |
| Database | PostgreSQL (Neon) | — |

## Request lifecycle (identify)

1. `POST /api/v1/identify` receives a multipart image upload.
2. `ml.preprocessing.decode_image` validates content type/size/dimensions.
3. `FaceRecognitionPipeline.process` runs YuNet detection, enforces exactly-one-face,
   runs SFace embedding, L2-normalizes.
4. `IdentityRepository.get_all_samples` loads every enrolled embedding.
5. `ml.matching.best_match` computes cosine similarity against every sample, takes the
   max per identity, and applies the frozen threshold gate.
6. A `recognition_events` row is logged (outcome, candidate id, score — no image data).
7. Response: `{"outcome": "known", ...}` or `{"outcome": "unknown"}` — Unknown never
   reveals a candidate identity.

Errors (`NoFaceDetectedError`, `MultipleFacesDetectedError`, `InvalidImageError`) are
caught by FastAPI exception handlers in `backend/app/main.py` and translated into safe,
actionable JSON responses — never a stack trace or SQL error.
