import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_face_recognition.db"
os.environ["STORAGE_BACKEND"] = "memory"
os.environ["RECOGNITION_BACKEND"] = "demo"
os.environ["SECRET_KEY"] = "test-secret"

from app.db.base import Base
from app.db.session import build_engine
from app.main import create_app
from app.models import User


class FakePipeline:
    backend_name = "test"
    model_name = "test-embedder"

    def process_image(self, image_bytes, threshold):
        _ = image_bytes
        _ = threshold
        from app.services.recognition.base import RecognitionResult

        return RecognitionResult(
            status="processed",
            similarity_score=None,
            threshold_used=0.86,
            confidence_band="none",
            reason_codes=[],
            quality_score=0.95,
            backend_name=self.backend_name,
            model_name=self.model_name,
            embedding=[1.0, 0.0, 0.0],
        )


class FakeVerificationService:
    def __init__(self):
        self.pipeline = FakePipeline()
        self.backend_name = self.pipeline.backend_name
        self.model_name = self.pipeline.model_name

    def current_threshold(self, db):
        _ = db
        return 0.86

    def verify(self, db, *, image_bytes, candidate_user_id=None):
        _ = image_bytes
        result = self.pipeline.process_image(b"", 0.86)
        statement = select(User).where(User.is_active.is_(True))
        if candidate_user_id is not None:
            statement = statement.where(User.id == candidate_user_id)
        user = db.scalar(statement)
        if user is None:
            result.status = "unmatched"
            result.reason_codes = ["no_enrollments"]
            result.confidence_band = "low"
            return result, None
        result.status = "matched"
        result.reason_codes = ["matched"]
        result.similarity_score = 0.99
        result.confidence_band = "high"
        return result, user


@pytest.fixture
def client():
    app = create_app()
    app.state.verification_service = FakeVerificationService()
    engine = build_engine(app.state.settings)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        response = test_client.post(
            "/login",
            data={"username": "admin", "password": "Admin123!"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        yield test_client
    db_path = Path("test_face_recognition.db")
    if db_path.exists():
        db_path.unlink()
