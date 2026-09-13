# Security & Privacy Baseline

This is an AI/ML internship assignment prototype. **It is not high-assurance biometric
authentication** — there is no liveness detection, no identity proofing, and no
security review beyond what is documented here.

## Data handling

- Raw uploaded images are decoded in-memory for detection/embedding and are **never
  written to disk or logged**.
- Only face **embeddings** (128-dim float vectors) are persisted, alongside an
  identity's display name and timestamps.
- `recognition_events` stores outcome/candidate-id/score/timestamp for operational
  visibility — never the query image itself.
- Deleting an identity (`DELETE /api/v1/identities/{id}`) cascades to delete all of
  its stored embeddings.

## Input validation

- `ml/preprocessing.py` rejects empty files, oversized files (>8MB), corrupt/unsupported
  formats, and images below a minimum resolution before any model runs.
- Identity name length is bounded server-side (`Form(..., max_length=255)`).

## Safe errors

- All expected failure modes (no face, multiple faces, invalid image, missing identity)
  return structured JSON with a generic, user-safe message — see the exception handlers
  in `backend/app/main.py`.
- Unhandled exceptions are caught by a catch-all handler that logs the exception type
  and returns a generic 500 with no internal details (no stack trace, no SQL, no file
  paths) to the client.

## Rate limiting

- `/api/v1/enroll` and `/api/v1/identify` are rate-limited per client IP via an
  in-memory sliding window (`backend/app/core/rate_limit.py`).
- **Known limitation:** this is single-process only. A multi-instance deployment would
  need a shared store (e.g. Redis) for the limiter to be effective.

## Secrets

- The database connection string lives in `.env` (gitignored) and is loaded via
  `pydantic-settings`. No credentials are committed to the repository.
- `.env.example` documents the required variables with placeholder values only.

## CORS

- `CORSMiddleware` restricts allowed origins to `CORS_ALLOWED_ORIGINS` (defaults to the
  local Vite dev origins). Update this to the deployed frontend origin in production.

## Known gaps (not implemented — documented, not hidden)

- **No authentication/authorization.** The `/api/v1/identities` list/delete endpoints
  are open. This is acceptable for a local/demo assignment context but **must not** be
  exposed publicly without adding an auth layer (ADR-009).
- **No liveness/anti-spoofing.** A printed photo or screen replay would currently pass
  detection and matching. Out of scope for this assignment (PRD Non-Goals).
- **No audit trail for admin deletions** beyond standard database state.
