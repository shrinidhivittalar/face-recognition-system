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

Two thresholds, calibrated separately because the cost of being wrong differs:

| Decision | Threshold | Optimised for |
|---|---|---|
| **Identification** — is this query one of the enrolled people? | **0.2975** | FAR ≤ 1% |
| **Duplicate enrollment** — is this new person already enrolled? | **0.3426** | Near-zero wrongful blocks |

The duplicate gate is stricter on purpose. A false accept during identification
mislabels someone; a false accept during enrollment *prevents a legitimate new
user from enrolling at all*. Reusing 0.2975 would wrongly block 0.859% of new
enrollments (8 per 931 on held-out data); 0.3426 reduces that to 0.215% (2 per
931) while still catching 99.25% of genuine duplicates. Derived by
`scripts/run_duplicate_threshold_experiment.py`; evidence in
`data/duplicate_threshold_results.json`.

The identification threshold below is unchanged.

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
pip install -r requirements-dev.txt  # evaluation needs pyarrow + matplotlib
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

## Scope, Limitations & Future Work

This is a small-scale face recognition **identification** system built within the
assignment's three-day and zero-cost constraints. It is not a production biometric
authentication product, and the gaps below are stated deliberately rather than
left implicit.

### Implemented and verified

The core pipeline and the engineering around it are complete and exercised by
tests and by manual verification against the containerised stack:

- YuNet detection → exactly-one-face policy → SFace embeddings → L2 normalization
  → cosine similarity → calibrated threshold gate.
- **Unknown rejection**, including the guarantee that a rejected match never
  discloses the closest candidate identity.
- Threshold **empirically calibrated** on held-out LFW pairs, with a reproducible
  harness (`scripts/run_evaluation.py`) that regenerates the reported figures.
- PostgreSQL persistence behind a repository interface, with cascade deletion of
  an identity's embeddings.
- Server-side input validation and a safe error contract — no stack traces, SQL,
  or internal paths reach clients.
- React UI covering enrollment, identification, Known/Unknown results, and error
  states.
- Docker packaging, CI (pytest + frontend build) on every push, and a public
  deployment.

### Current limitations

- **No liveness or presentation-attack detection.** A printed photo, a screen
  replay, or a mask would be processed as a genuine face. This is the single
  largest reason the system must not be treated as an authentication mechanism.
- **The threshold is dataset-calibrated, not deployment-calibrated.** 0.2975 was
  derived from LFW, which skews toward frontal, well-lit, adult, public-figure
  photography. Accuracy on a different population, camera, or lighting regime is
  unmeasured, and the operating point would need re-derivation from
  representative data before real use.
- **Evaluation covers verification pairs, not the deployed task.** FAR/FRR are
  measured pairwise; the system performs 1:N identification against the enrolled
  set, where false-accept probability grows with population size. No demographic
  or subgroup breakdown was performed.
- **No authentication or authorization.** The identity list/delete endpoints are
  unauthenticated. Acceptable for a local demo; not safe to expose publicly as-is.
- **Matching is a full scan.** Every identification loads all stored embeddings
  and compares them in application memory. Correct and fast at demo scale,
  linearly worse as enrollment grows.
- **Single-process rate limiting.** The limiter holds state in memory, so it is
  ineffective across multiple instances.
- **Observability is logs only.** Structured logs and a `recognition_events`
  audit trail exist; there are no metrics, tracing, or alerting.
- **Embedding versioning is recorded but not managed.** Each embedding stores its
  `model_version`, yet nothing re-embeds or migrates existing records if the model
  changes, and mixing versions in one comparison would be silently invalid.
- **Duplicate detection can wrongly block a legitimate new user.** At the 0.3426
  gate, roughly 0.2% of genuinely distinct people resemble an enrolled person
  closely enough to be refused. Because the response deliberately withholds the
  matching identity, an affected user cannot self-diagnose or resolve it — an
  operator would have to intervene, and no such workflow exists.
- **Free-tier hosting constraints.** The deployed instance sleeps after inactivity
  and cold-starts in roughly a minute; it is a single instance with no redundancy.

### Intentionally out of scope

Deliberately excluded to protect the mandatory ML pipeline and the deadline —
these are what production hardening would require, not unfinished work:

- **Presentation-attack detection** (passive or challenge-response liveness),
  plus identity proofing at enrollment, before any authentication claim.
- **Deployment-specific evaluation:** re-calibration on representative captured
  data, 1:N identification metrics at realistic population sizes, subgroup
  fairness analysis, and a scheduled re-validation cadence.
- **Production auth:** authenticated sessions and role-based access control
  enforced server-side, with audited administrative actions.
- **Biometric data governance:** documented retention and deletion policy,
  subject access and erasure workflows, encryption of embeddings at rest, and
  consent capture appropriate to the jurisdiction.
- **Operational monitoring:** metrics, distributed tracing, alerting on error and
  latency budgets, and drift monitoring on score distributions.
- **Model lifecycle:** versioned model artifacts with a re-embedding and
  backfill path, refusal to compare across incompatible versions, and
  shadow-evaluation before promotion.
- **Scalable matching:** an approximate nearest-neighbour index (for example
  pgvector or FAISS) once linear scan stops being adequate.
- **Availability and scale:** multiple instances behind a load balancer, shared
  rate-limit state, connection pooling tuned for concurrency, and no cold starts.

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
| `POST /api/v1/enroll` | Multipart `display_name` + `image`; creates identity + first embedding. Returns `409 duplicate_identity` if the face is already enrolled, without naming the existing identity |
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
# requirements-dev.txt = runtime deps + test/evaluation tooling.
# Use requirements.txt alone if you only want to serve the API.
./.venv/Scripts/pip install -r requirements-dev.txt      # Windows
# source .venv/bin/pip install -r requirements-dev.txt   # macOS/Linux

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
