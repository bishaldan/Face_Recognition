import base64
from io import BytesIO

import numpy as np
from PIL import Image


def make_data_url(color: int = 120) -> str:
    image = Image.fromarray(np.full((300, 300, 3), color, dtype=np.uint8))
    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_system_info_endpoint(client):
    response = client.get("/api/system/info")
    assert response.status_code == 200
    body = response.json()
    assert body["recognition_backend"] == "test"
    assert body["storage_backend"] == "memory"
    assert body["database_engine"] == "sqlite"


def test_enrollment_requires_consent(client):
    response = client.post(
        "/api/enrollments/start",
        json={"full_name": "Test User", "email": None, "notes": None, "consent_given": False},
    )
    assert response.status_code == 400


def test_user_listing_after_enrollment(client):
    start = client.post(
        "/api/enrollments/start",
        json={"full_name": "Alice Example", "email": "alice@example.com", "notes": "", "consent_given": True},
    )
    session_id = start.json()["session_id"]

    for _ in range(3):
        client.post(f"/api/enrollments/{session_id}/captures", json={"image_data": make_data_url(160)})

    finalize = client.post(
        f"/api/enrollments/{session_id}/finalize",
        json={"session_id": session_id},
    )
    assert finalize.status_code == 200
    users = client.get("/api/users")
    assert users.status_code == 200
    assert any(user["full_name"] == "Alice Example" for user in users.json())
