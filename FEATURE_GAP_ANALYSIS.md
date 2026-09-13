# Feature Gap Analysis

A product-completeness audit of this face recognition identification system —
distinct from the correctness audit already reflected in the test suite. The
question here is not "is the code right" but "does this do what someone using a
face recognition system would expect, and where it doesn't, how much does that
actually cost them."

Assessed at commit `969b338`. Scope context: a three-day, zero-cost assignment,
so several gaps below are legitimately out of scope — they are marked as such
rather than counted against the build.

---

## 1. What genuinely works

Verified end-to-end against the containerised stack and the deployed instance,
not inferred from the UI looking complete:

| Capability | Status |
|---|---|
| YuNet detection → exactly-one-face → SFace embedding → cosine similarity → threshold gate | Fully wired |
| Enrollment (identity + first embedding) | Fully wired, real Postgres |
| Identification returning Known | Fully wired |
| Unknown rejection, with no candidate disclosure | Fully wired |
| Rejection of 0-face and 2+-face images | Fully wired |
| Invalid/corrupt/oversized image rejection | Fully wired |
| Identity list and delete (cascades to embeddings) | Fully wired |
| Persistence | Real backend — Neon PostgreSQL, survives restart and redeploy |

This is a real application, not a mock. State survives a cache clear, a second
device, and a container rebuild. The core value loop — enroll a person, later
recognise them, correctly refuse strangers — is genuinely closed.

---

## 2. Wired in the backend, absent from the product

The most important findings are not missing code. They are capabilities that
exist, are tested, and are reachable by API — but that no user can actually
reach through the interface.

| Capability | Backend | API client | UI | Reality |
|---|---|---|---|---|
| Add extra face samples to an identity | ✅ implemented + tested | ✅ `addSample()` | ✅ **resolved** — see below | Reachable |
| Recognition audit history | ✅ written every identify | ❌ no read method | ❌ | Write-only data |
| Health/status surface | ✅ `/health` | ✅ `checkHealth()` | ❌ **0 call sites** | Unreachable |
| Detection quality score | ✅ computed + returned | ✅ in response type | ❌ never rendered | Discarded |

> **Resolved — multi-sample enrollment.** Originally the highest-severity finding
> in this document (§3.1): the backend honoured FR-02 but no user could reach it.
> Now exposed via `AddSampleCapture`, used in two places — on the enrollment
> success screen to strengthen a new identity immediately, and from the Admin
> table to add photos to an existing one, which is the recovery path for someone
> being wrongly reported Unknown. Verified end to end: sample count increments
> 1 → 2, identification still resolves, and a multi-face image is rejected 422.
> §3.1 is retained below as the rationale for the change.

`checkHealth` remains defined in `frontend/src/api/client.ts` and called from
nowhere in `pages/` or `components/`. `RecognitionEventRepository` still has
exactly one method, `log_event` — no read path anywhere in the backend, no
endpoint, and no screen.

Other absences:

- **No identity detail view** — cannot inspect an enrolled person, see how many
  samples they have (beyond a count in the list), or manage those samples.
- **No re-enrollment or update flow** — the only remediation for a bad
  enrollment is delete and start over.
- **`GET /api/v1/identities` is unbounded** — no pagination, limit, or search.
  Fine at demo scale, degrades linearly.
- **No consent capture** at enrollment, despite storing biometric derivatives.

---

## 3. Why the top gaps matter

### 3.1 Single-sample enrollment is the most damaging gap — *now resolved*

> **Status: addressed.** Retained here because the reasoning is what justified
> the fix, and because the underlying accuracy caveat still stands: multiple
> samples are now *possible*, but nothing *requires* them, so an identity
> enrolled from one photo remains as fragile as described below.

This is the one that breaks the core loop for a real user.

The PRD lists **FR-02 Multiple Enrollment Samples** as a MUST, and the backend
honours it — multiple embeddings per identity, max-similarity aggregation, an
endpoint, passing tests. But enrollment in the UI captures exactly one image,
and there is no path to add another. The capability is complete everywhere
except where a user could touch it.

The causal chain:

1. A user enrolls with one webcam frame — whatever pose and lighting they had.
2. Reported accuracy (FRR 0.54%) comes from LFW: frontal, well-lit, professional
   photography. A single opportunistic webcam capture is not that.
3. Later, the same person is told **Unknown** because they tilted their head,
   changed lighting, or wore glasses.
4. The user's conclusion is not "my enrollment sample was weak." It is
   **"this system doesn't recognise me"** — the product's one job.
5. There is no recovery action in the UI. They cannot strengthen their
   enrollment. They can only delete themselves and gamble on a better photo.

AWS recommends indexing **at least five images** per person spanning varied yaw
and pitch, precisely because single-sample enrollment generalises poorly.[^1]
Aggregating multiple face vectors per user is their documented accuracy
improvement.[^2] Our system already implements the hard half of that and hides it.

**Effort: rewire, not build.** The endpoint, client function, aggregation logic
and tests exist. This needs a screen, not a subsystem.

### 3.2 No quality gate lets a bad enrollment poison an identity silently

Enrollment accepts any image yielding exactly one face above detector confidence
0.9. That threshold answers "is this a face," not "is this a face worth
enrolling." A dark, motion-blurred, or extreme-angle capture is accepted without
comment.

The failure is delayed and misattributed: nothing looks wrong at enrollment, and
the consequence appears later as unexplained Unknowns — which a user blames on
recognition, not on the enrollment they completed successfully days earlier.

Azure exposes `qualityForRecognition` for exactly this, and recommends admitting
**only high-quality images for enrollment** and medium-or-better for
identification.[^3] Notably, we already compute and return a `detection_score`
in every enroll response — the UI simply discards it. That is a weak proxy for
image quality, but the plumbing to surface *something* is already there.

**Effort: partial build.** A real quality signal (blur, exposure, pose) is new
work; gating on the score we already return is not.

### 3.3 Liveness — real, but correctly scoped out

A printed photo or phone screen replay would be accepted. Commercial liveness
solutions are benchmarked against iBeta Level 1/2 presentation-attack testing.[^4]

Severity depends on framing, and the distinction matters. This system performs
**identification** ("who is this?"), not **authentication** ("prove you are who
you claim, to grant access"). Spoofing an identification demo yields a wrong
label; spoofing an authentication gate yields unauthorised access. The absence
is disqualifying for the second use case and merely a limitation for the first.

Already documented in the README and `docs/SECURITY.md`, and explicitly a PRD
non-goal. Listed here for completeness, not as an oversight.

**Effort: build from zero**, including an additional model.

### 3.4 Audit data is collected and unreadable

Every identification writes a `recognition_events` row: outcome, candidate
identity, similarity score, timestamp. Nothing ever reads it.

Two costs. Operationally, the data that would answer "is accuracy degrading?"
or "how often are we returning Unknown?" accumulates unused. From a privacy
standpoint, it is worse: the system retains a per-identification behavioural
record with no way to view, export, or purge it independently of deleting the
identity. Deleting an identity sets `candidate_identity_id` to NULL via
`ondelete="SET NULL"` — the event row itself, with its score and timestamp,
persists indefinitely.

For a system handling biometric derivatives, "we log it and cannot show you"
is a governance gap, not just a missing screen.

**Effort: rewire.** A read method, an endpoint, a table.

---

## 4. Gaps against industry practice

Benchmarked against AWS Rekognition and Azure Face — the closest real
equivalents to what this system does.

| Practice in real products | Here | Assessment |
|---|---|---|
| ≥5 enrollment images, varied pose[^1] | Multi-sample now supported and prompted for; not enforced | **Partly closed** — §3.1 |
| Quality gating before enrollment[^3] | Detector confidence only | **Real gap** — §3.2 |
| Presentation-attack detection[^4] | None | Out of scope, documented |
| Meaningful consent at enrollment, opt-out of photo storage[^5] | No consent UI | **Real gap** for biometric data |
| Admin override of quality filters for users who can't enroll[^5] | N/A (no filters) | Follows from §3.2 |
| Aggregating multiple vectors into a user vector[^2] | Max-similarity across samples | **Implemented** — reasonable equivalent |
| Not storing raw images | Embeddings only, images never persisted | **Implemented**, exceeds baseline |
| Withholding candidate identity on no-match | Enforced and tested | **Implemented** |

Two rows deserve credit rather than criticism: never persisting raw face images,
and refusing to leak the nearest candidate on an Unknown result, are both
choices real products get wrong and this one gets right.

---

## Summary

The ML core is complete and the engineering around it is real. The gaps
concentrate in one specific place: **capabilities that exist in the backend but
have no route to a user.**

Multi-sample enrollment was the clearest and most damaging instance — a stated
MUST requirement, fully built, and completely unreachable. It has since been
exposed in the UI, which also confirmed the wider point: it took a component and
two call sites, no backend change, because the capability was already there.

Remaining in that category: the recognition audit history (write-only) and the
health surface (client function with no screen). Both are rewiring rather than
construction. Liveness is the only item in this analysis that would require
building a new capability from zero, and it is the one legitimately excluded by
scope.

---

## Sources

[^1]: [Recommendations for facial input images — Amazon Rekognition](https://docs.aws.amazon.com/rekognition/latest/dg/recommendations-facial-input-images-search.html)
[^2]: [Associating faces to a user — Amazon Rekognition](https://docs.aws.amazon.com/rekognition/latest/dg/associate-faces.html)
[^3]: [Face detection, attributes, and input data — Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/face/concept-face-detection)
[^4]: [Face liveness detection — Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/face/concept-face-liveness-detection)
[^5]: [Best practices for adding users to a Face service — Microsoft Learn](https://learn.microsoft.com/en-us/azure/ai-services/face/enrollment-overview)
