# User Flows

## Enrollment

Home → Enroll Person → enter identity name → camera capture / upload → submit →
backend validation → face detection → exactly-one-face check → SFace embedding →
persist identity + embedding → success screen ("Enroll Another" / "Go to Identify").

Error branches: no face, multiple faces, invalid image, processing failure — each
shown with an actionable, specific message (never a raw stack trace).

## Identification

Home → Identify Face → camera capture / upload → backend validation → face detection →
exactly-one-face check → SFace embedding → cosine similarity search across all enrolled
samples → threshold gate → **Known** (display name shown, raw score not surfaced) or
**Unknown** (no candidate identity revealed, ever) → "Identify Again" / "Enroll Person".

## Admin (no auth — see docs/SECURITY.md)

Admin page → list enrolled identities with sample counts → remove an identity (cascades
to its embeddings).
