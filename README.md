# Face Recognition Identification System

An AI/ML internship assignment: enroll people, then identify a new photo against the
enrolled set, rejecting insufficient matches as **Unknown**. Built with a
production-oriented (not production-scale) architecture: React + FastAPI + PostgreSQL,
with the ML core isolated behind clean interfaces.

This is an identification **prototype**, not a high-assurance biometric authentication
product — see [`docs/SECURITY.md`](docs/SECURITY.md) for the full disclaimer and
known limitations.

## Model & Matching

| Component | Choice |
|---|---|
| Face detection | [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) (`face_detection_yunet_2023mar.onnx`), MIT licensed |
| Face recognition / embeddings | [SFace](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface) (`face_recognition_sface_2021dec.onnx`), Apache-2.0 licensed |
| Runtime | OpenCV's native `FaceDetectorYN` / `FaceRecognizerSF` (ONNX under the hood) |
| Similarity | Cosine similarity on L2-normalized 128-d embeddings |
| Face-count policy | Exactly one face required for enrollment and identification; 0 or 2+ faces are rejected, never silently resolved |
| Multi-sample aggregation | Max similarity across an identity's stored samples ("best-sample-wins") |

YuNet+SFace was chosen for permissive licensing, small footprint (~37MB combined,
free-tier deployable), and implementation speed within a 3-day window — not asserted as
the universally best recognition model available. See
[`docs/ADR/ADR-REGISTER.md`](docs/ADR/ADR-REGISTER.md) for the full rationale and every
other frozen decision.

## Matching Threshold

**Frozen at 0.2975**, calibrated empirically — never hand-picked. Methodology:

1. Loaded the standard LFW "View 1" verification pairs protocol (1,000 calibration
   pairs, 2,200 held-out test pairs; genuine vs. impostor pairs are pre-labeled).
2. Ran every image through the same detection→embedding pipeline used in production.
3. Swept candidate thresholds on the **calibration** split only, computing FAR
   (False Acceptance Rate) and FRR (False Rejection Rate) at each.
4. Selected the lowest threshold keeping FAR ≤ 1% (prioritizing meaningful Unknown
   rejection while retaining useful recognition), then froze it.
5. Applied the frozen threshold to the **held-out** test split (pairs never seen during
   selection) to get an honest performance estimate.

**Held-out test result: FAR 0.86%, FRR 0.54%, accuracy 99.30%** (929 genuine / 931
impostor pairs scored). Full numbers, dataset provenance, and limitations:
[`docs/EVALUATION.md`](docs/EVALUATION.md). Raw results: `data/evaluation_results.json`.
Score distribution plot: `data/score_distribution.png`.

Reproduce it yourself:
```bash
python scripts/download_dataset.py   # fetches LFW pairs (~84MB, not committed)
python scripts/run_evaluation.py     # re-runs calibration + evaluation end-to-end
```

## Failure Cases

Documented and measured, not swept under the rug:

- **False acceptance (0.86% on held-out data):** look-alike pairs whose embeddings
  happen to fall above threshold. Inherent to any similarity-based system; the
  threshold trades this off against false rejection.
- **False rejection (0.54% on held-out data):** genuine pairs (same person, different
  photo) whose similarity fell below threshold — typically due to lighting, pose, or
  image quality differences between the two photos.
- **Exactly-one-face rejections:** ~15% of LFW pairs were excluded from scoring entirely
  because one or both images failed the exactly-one-face policy — mostly images
  containing a partially visible bystander, correctly refused rather than silently
  resolved. See `docs/EVALUATION.md` for the breakdown.
- **No liveness detection:** a printed photo or screen replay of an enrolled person's
  face would currently be accepted. Out of scope per the assignment's non-goals.
- **Threshold is dataset-calibrated, not population-calibrated:** it's tuned on LFW
  (celebrity photography, frontal/well-lit), not on this system's actual enrolled
  users. Re-calibration is recommended before any real deployment.

## Improvements (if given more time)

- Calibrate the threshold against a captured dataset of the system's actual target
  users/cameras, not just LFW.
- Add liveness/anti-spoofing (e.g. blink detection, texture analysis) before claiming
  any authentication use case.
- Move the rate limiter to a shared store (Redis) for multi-instance deployments.
- Add authentication/RBAC in front of the admin identity-management endpoints.
- Add a pgvector-backed similarity search if the enrolled population grows large enough
  that per-request full-table cosine similarity becomes a bottleneck.
- CI (GitHub Actions) running the pytest suite and frontend build on every push.

## Architecture

```
React UI  -->  FastAPI  -->  Recognition Service  -->  Repository  -->  PostgreSQL (Neon)
                                    |
                            YuNet + SFace (ONNX, via OpenCV)
```

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) ·
[`docs/DATA_FLOW.md`](docs/DATA_FLOW.md) ·
[`docs/USER_FLOWS.md`](docs/USER_FLOWS.md) ·
[`docs/SECURITY.md`](docs/SECURITY.md)

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Health/status check (API + DB + model version) |
| `POST /api/v1/enroll` | Multipart `display_name` + `image`; creates identity + first embedding |
| `POST /api/v1/identities/{id}/samples` | Add another sample/embedding to an existing identity |
| `POST /api/v1/identify` | Multipart `image`; returns `{"outcome": "known", identity_id, display_name}` or `{"outcome": "unknown"}` — never leaks a candidate identity on Unknown |
| `GET /api/v1/identities` | List enrolled identities (no auth — demo/admin only, see Security) |
| `DELETE /api/v1/identities/{id}` | Remove an identity and its embeddings |

## Running Locally

Everything Python lives in a local virtual environment — nothing is installed globally,
so deleting the project folder removes all dependencies.

### 1. Backend

```bash
python -m venv .venv
./.venv/Scripts/pip install -r requirements.txt      # Windows
# source .venv/bin/pip install -r requirements.txt   # macOS/Linux

cp .env.example .env
# Edit .env: paste a PostgreSQL connection string (a free Neon.tech project works well)

python scripts/init_db.py                             # create tables
./.venv/Scripts/python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # defaults to http://localhost:8000
npm run dev             # http://localhost:5173
```

### 3. Tests

```bash
./.venv/Scripts/python -m pytest              # ML unit tests + API tests (needs DB configured)
```

### Docker (alternative)

```bash
docker-compose up --build
```

Runs a local PostgreSQL container + the backend API together (`docker-compose.yml`).
Point the frontend's `VITE_API_BASE_URL` at `http://localhost:8000`.

## Repository Structure

```
face_reco/
├── frontend/           React + TypeScript UI (Vite)
├── backend/app/        FastAPI app: api/, core/, models/, repositories/, schemas/, services/
├── backend/tests/      API tests (pytest, run against a real Postgres DB)
├── ml/                 Detection, embedding, matching, model adapter
├── ml/evaluation/      Threshold calibration harness (dataset, pairs, metrics, threshold, report)
├── tests/              ML unit tests + small offline image fixtures
├── models/             YuNet + SFace ONNX weights + their LICENSE files
├── data/                evaluation_results.json, score_distribution.png (raw LFW pairs gitignored)
├── docs/                ADR register, architecture, data/user flows, security
├── scripts/             download_dataset.py, run_evaluation.py, init_db.py
├── docker-compose.yml
└── .env.example
```

## Scope Notes

Company-mandated requirements (enrollment, detection, embeddings, similarity matching,
Unknown rejection, evaluation, README, $0 budget, 3-day deadline, public GitHub repo)
are treated as frozen and non-negotiable. Everything else here — the tech stack, the UI
design, PostgreSQL, Docker, the admin page — is an engineering decision made to
demonstrate practice, not something the assignment brief asked for. Full breakdown in
[`docs/ADR/ADR-REGISTER.md`](docs/ADR/ADR-REGISTER.md).
