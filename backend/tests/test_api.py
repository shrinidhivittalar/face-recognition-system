from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["database"] == "ok"


def test_enroll_valid_face_succeeds(client):
    resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["display_name"] == "Alice"
    assert "identity_id" in body


def test_enroll_no_face_rejected(client):
    import io
    import numpy as np
    import cv2

    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    ok, buf = cv2.imencode(".jpg", blank)
    resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Nobody"},
        files={"image": ("blank.jpg", io.BytesIO(buf.tobytes()), "image/jpeg")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "no_face"


def test_enroll_multiple_faces_rejected(client):
    resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Group"},
        files={"image": ("two.jpg", fixture_bytes("two_faces.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "multiple_faces"


def test_identify_known_person(client):
    enroll_resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    assert enroll_resp.status_code == 200
    identity_id = enroll_resp.json()["identity_id"]

    identify_resp = client.post(
        "/api/v1/identify",
        files={"image": ("a2.jpg", fixture_bytes("single_face_a2.jpg"), "image/jpeg")},
    )
    assert identify_resp.status_code == 200
    body = identify_resp.json()
    assert body["outcome"] == "known"
    assert body["identity_id"] == identity_id
    assert body["display_name"] == "Alice"


def test_identify_unrelated_person_returns_unknown_without_leaking_candidate(client):
    client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )

    identify_resp = client.post(
        "/api/v1/identify",
        files={"image": ("b1.jpg", fixture_bytes("single_face_b1.jpg"), "image/jpeg")},
    )
    assert identify_resp.status_code == 200
    body = identify_resp.json()
    assert body["outcome"] == "unknown"
    assert body["identity_id"] is None
    assert body["display_name"] is None


def test_identify_with_no_enrolled_identities_returns_unknown(client):
    resp = client.post(
        "/api/v1/identify",
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["outcome"] == "unknown"


def test_add_sample_to_existing_identity(client):
    enroll_resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    identity_id = enroll_resp.json()["identity_id"]

    sample_resp = client.post(
        f"/api/v1/identities/{identity_id}/samples",
        files={"image": ("a2.jpg", fixture_bytes("single_face_a2.jpg"), "image/jpeg")},
    )
    assert sample_resp.status_code == 200
    assert sample_resp.json()["identity_id"] == identity_id


def test_add_sample_to_missing_identity_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.post(
        f"/api/v1/identities/{fake_id}/samples",
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 404


def test_list_identities(client):
    client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    resp = client.get("/api/v1/identities")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["display_name"] == "Alice"
    assert body[0]["sample_count"] == 1


def _enroll(client, name, fixture):
    return client.post(
        "/api/v1/enroll",
        data={"display_name": name},
        files={"image": (fixture, fixture_bytes(fixture), "image/jpeg")},
    )


def test_duplicate_enrollment_exact_same_image_rejected(client):
    assert _enroll(client, "Alice", "single_face_a1.jpg").status_code == 200

    resp = _enroll(client, "Bob", "single_face_a1.jpg")
    assert resp.status_code == 409
    assert resp.json()["error"] == "duplicate_identity"


def test_duplicate_enrollment_different_image_same_person_rejected(client):
    assert _enroll(client, "Alice", "single_face_a1.jpg").status_code == 200

    resp = _enroll(client, "Alice Again", "single_face_a2.jpg")
    assert resp.status_code == 409
    assert resp.json()["error"] == "duplicate_identity"


def test_duplicate_response_does_not_disclose_existing_identity(client):
    enrolled = _enroll(client, "Alice", "single_face_a1.jpg")
    identity_id = enrolled.json()["identity_id"]

    resp = _enroll(client, "Bob", "single_face_a1.jpg")
    body = resp.text

    assert "Alice" not in body
    assert identity_id not in body
    assert set(resp.json().keys()) == {"error", "message"}


def test_duplicate_rejection_creates_no_partial_identity(client):
    _enroll(client, "Alice", "single_face_a1.jpg")
    _enroll(client, "Bob", "single_face_a1.jpg")

    identities = client.get("/api/v1/identities").json()
    assert [i["display_name"] for i in identities] == ["Alice"]


def test_genuinely_different_person_still_enrolls(client):
    assert _enroll(client, "Alice", "single_face_a1.jpg").status_code == 200

    resp = _enroll(client, "Different Person", "single_face_b1.jpg")
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "Different Person"


def test_adding_sample_to_existing_identity_is_not_blocked_as_duplicate(client):
    """The duplicate gate must never interfere with the add-sample path."""
    enrolled = _enroll(client, "Alice", "single_face_a1.jpg")
    identity_id = enrolled.json()["identity_id"]

    resp = client.post(
        f"/api/v1/identities/{identity_id}/samples",
        files={"image": ("a2.jpg", fixture_bytes("single_face_a2.jpg"), "image/jpeg")},
    )
    assert resp.status_code == 200

    identities = client.get("/api/v1/identities").json()
    assert identities[0]["sample_count"] == 2


def test_identification_unaffected_by_duplicate_gate(client):
    """Duplicate detection must not change who gets identified."""
    enrolled = _enroll(client, "Alice", "single_face_a1.jpg")
    identity_id = enrolled.json()["identity_id"]

    known = client.post(
        "/api/v1/identify",
        files={"image": ("a2.jpg", fixture_bytes("single_face_a2.jpg"), "image/jpeg")},
    )
    assert known.json()["outcome"] == "known"
    assert known.json()["identity_id"] == identity_id

    unknown = client.post(
        "/api/v1/identify",
        files={"image": ("b1.jpg", fixture_bytes("single_face_b1.jpg"), "image/jpeg")},
    )
    assert unknown.json()["outcome"] == "unknown"
    assert unknown.json()["identity_id"] is None


def test_delete_identity(client):
    enroll_resp = client.post(
        "/api/v1/enroll",
        data={"display_name": "Alice"},
        files={"image": ("a1.jpg", fixture_bytes("single_face_a1.jpg"), "image/jpeg")},
    )
    identity_id = enroll_resp.json()["identity_id"]

    delete_resp = client.delete(f"/api/v1/identities/{identity_id}")
    assert delete_resp.status_code == 204

    list_resp = client.get("/api/v1/identities")
    assert list_resp.json() == []
