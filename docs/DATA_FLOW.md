# Data Flow

```
Image bytes (multipart upload)
        |
        v
ml.preprocessing.decode_image        -- validate size/dims/format, decode to BGR ndarray
        |
        v
ml.detector.FaceDetector.detect      -- YuNet, returns 0..N face boxes + landmarks
        |
        v
exactly-one-face policy              -- 0 -> NoFaceDetectedError, 2+ -> MultipleFacesDetectedError
        |
        v
ml.embedding.FaceEmbedder.embed      -- SFace alignCrop + feature extraction (128-d)
        |
        v
ml.embedding.normalize               -- L2 normalize
        |
   +----+----------------------------------------+
   |                                              |
   v (enrollment)                                 v (identification)
IdentityRepository.add_embedding             IdentityRepository.get_all_samples
   |                                              |
   v                                              v
PostgreSQL: face_embeddings row              ml.matching.best_match (cosine sim, max per identity)
                                                   |
                                                   v
                                              threshold gate (0.2975)
                                                   |
                                                   v
                                     RecognitionEventRepository.log_event
                                     (outcome, candidate_id, score -- no image data)
                                                   |
                                                   v
                                     API response: {"outcome": "known"|"unknown", ...}
```

No raw image bytes or embedding vectors are ever written to logs.
