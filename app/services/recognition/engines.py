import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import SystemSetting, User
from app.services.recognition.base import (
    BoundingBox,
    DetectedFace,
    FaceDetector,
    FaceEmbedder,
    RecognitionResult,
)
from app.services.recognition.quality import BasicQualityAssessor


def decode_data_url(image_data: str) -> bytes:
    _, encoded = image_data.split(",", maxsplit=1)
    return base64.b64decode(encoded)


def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
    image = np.array(pil_image)
    return cv2.cvtColor(image, cv2.COLOR_RGB2BGR)


def encode_image_bytes(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", image)
    if not ok:
        raise ValueError("Unable to encode image")
    return bytes(buffer.tobytes())


def cosine_similarity(lhs: list[float], rhs: list[float]) -> float:
    lhs_arr = np.asarray(lhs, dtype=np.float32)
    rhs_arr = np.asarray(rhs, dtype=np.float32)
    denom = float(np.linalg.norm(lhs_arr) * np.linalg.norm(rhs_arr))
    if denom == 0:
        return 0.0
    return float(np.dot(lhs_arr, rhs_arr) / denom)


class OpenCVHaarFaceDetector(FaceDetector):
    def __init__(self):
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)

    def detect(self, image: np.ndarray) -> list[DetectedFace]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60))
        detected: list[DetectedFace] = []
        for x, y, width, height in faces:
            padding = int(min(width, height) * 0.15)
            x0 = max(0, x - padding)
            y0 = max(0, y - padding)
            x1 = min(image.shape[1], x + width + padding)
            y1 = min(image.shape[0], y + height + padding)
            crop = image[y0:y1, x0:x1]
            detected.append(
                DetectedFace(bbox=BoundingBox(x=int(x0), y=int(y0), width=int(x1 - x0), height=int(y1 - y0)), crop=crop)
            )
        return detected


class DemoFaceEmbedder(FaceEmbedder):
    backend_name = "demo"
    model_name = "demo-histogram-v1"

    def embed(self, face_crop: np.ndarray) -> list[float]:
        resized = cv2.resize(face_crop, (64, 64))
        hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        normalized = cv2.normalize(hist, hist).flatten().astype(np.float32)
        return normalized.tolist()


class OnnxFaceEmbedder(FaceEmbedder):
    backend_name = "onnx"

    def __init__(self, model_path: str, input_size: int):
        try:
            import onnxruntime as ort
        except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "onnxruntime is required when RECOGNITION_BACKEND=onnx"
            ) from exc

        self.model_name = model_path.split("/")[-1]
        self.input_size = input_size
        self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name

    def embed(self, face_crop: np.ndarray) -> list[float]:
        resized = cv2.resize(face_crop, (self.input_size, self.input_size))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        tensor = rgb.astype(np.float32) / 127.5 - 1.0
        tensor = np.transpose(tensor, (2, 0, 1))[None, ...]
        output = self.session.run(None, {self.input_name: tensor})[0][0]
        norm = np.linalg.norm(output)
        if norm:
            output = output / norm
        return output.astype(np.float32).tolist()


class FaceRecognitionPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.detector = OpenCVHaarFaceDetector()
        self.quality = BasicQualityAssessor(settings)
        if settings.recognition_backend == "onnx" and settings.onnx_model_path:
            self.embedder: FaceEmbedder = OnnxFaceEmbedder(
                settings.onnx_model_path, settings.onnx_input_size
            )
        else:
            self.embedder = DemoFaceEmbedder()

    @property
    def backend_name(self) -> str:
        return self.embedder.backend_name

    @property
    def model_name(self) -> str:
        return self.embedder.model_name

    def process_image(self, image_bytes: bytes, threshold: float) -> RecognitionResult:
        image = decode_image_bytes(image_bytes)
        faces = self.detector.detect(image)
        if not faces:
            return RecognitionResult(
                status="rejected",
                similarity_score=None,
                threshold_used=threshold,
                confidence_band="none",
                reason_codes=["no_face"],
                quality_score=None,
                backend_name=self.backend_name,
                model_name=self.model_name,
            )
        if len(faces) > 1:
            return RecognitionResult(
                status="rejected",
                similarity_score=None,
                threshold_used=threshold,
                confidence_band="none",
                reason_codes=["multiple_faces"],
                quality_score=None,
                backend_name=self.backend_name,
                model_name=self.model_name,
            )

        face = faces[0]
        quality = self.quality.assess(image, face)
        if not quality.accepted:
            return RecognitionResult(
                status="rejected",
                similarity_score=None,
                threshold_used=threshold,
                confidence_band="none",
                reason_codes=["low_quality", *quality.reason_codes],
                quality_score=quality.score,
                backend_name=self.backend_name,
                model_name=self.model_name,
                bbox=face.bbox,
            )

        embedding = self.embedder.embed(face.crop)
        return RecognitionResult(
            status="processed",
            similarity_score=None,
            threshold_used=threshold,
            confidence_band="none",
            reason_codes=[],
            quality_score=quality.score,
            backend_name=self.backend_name,
            model_name=self.model_name,
            embedding=embedding,
            bbox=face.bbox,
        )


class VerificationService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.pipeline = FaceRecognitionPipeline(settings)

    @property
    def backend_name(self) -> str:
        return self.pipeline.backend_name

    @property
    def model_name(self) -> str:
        return self.pipeline.model_name

    def current_threshold(self, db: Session) -> float:
        record = db.get(SystemSetting, "default_similarity_threshold")
        if record is None:
            return self.settings.default_similarity_threshold
        return float(record.value)

    def candidate_users(self, db: Session, candidate_user_id: int | None = None) -> list[User]:
        statement = select(User).where(User.is_active.is_(True))
        if candidate_user_id is not None:
            statement = statement.where(User.id == candidate_user_id)
        return list(db.scalars(statement).unique())

    def verify(
        self, db: Session, *, image_bytes: bytes, candidate_user_id: int | None = None
    ) -> tuple[RecognitionResult, User | None]:
        threshold = self.current_threshold(db)
        processed = self.pipeline.process_image(image_bytes, threshold)
        if processed.embedding is None:
            return processed, None

        best_user: User | None = None
        best_score = -1.0
        for user in self.candidate_users(db, candidate_user_id=candidate_user_id):
            for embedding in user.embeddings:
                score = cosine_similarity(processed.embedding, embedding.vector)
                if score > best_score:
                    best_user = user
                    best_score = score

        processed.similarity_score = round(best_score, 4) if best_score >= 0 else None
        if best_user is None or best_score < threshold:
            processed.status = "unmatched"
            processed.confidence_band = "low"
            processed.reason_codes = ["below_threshold"] if best_score >= 0 else ["no_enrollments"]
            return processed, None

        processed.status = "matched"
        processed.reason_codes = ["matched"]
        if best_score >= threshold + 0.1:
            processed.confidence_band = "high"
        elif best_score >= threshold + 0.03:
            processed.confidence_band = "medium"
        else:
            processed.confidence_band = "low"
        return processed, best_user
