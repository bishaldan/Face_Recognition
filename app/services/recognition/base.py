from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass(slots=True)
class BoundingBox:
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True)
class DetectedFace:
    bbox: BoundingBox
    crop: np.ndarray


@dataclass(slots=True)
class QualityReport:
    accepted: bool
    score: float
    reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RecognitionResult:
    status: str
    similarity_score: float | None
    threshold_used: float
    confidence_band: str
    reason_codes: list[str]
    quality_score: float | None
    backend_name: str
    model_name: str
    embedding: list[float] | None = None
    bbox: BoundingBox | None = None


class FaceDetector(Protocol):
    def detect(self, image: np.ndarray) -> list[DetectedFace]: ...


class FaceEmbedder(Protocol):
    backend_name: str
    model_name: str

    def embed(self, face_crop: np.ndarray) -> list[float]: ...


class QualityAssessor(Protocol):
    def assess(self, image: np.ndarray, face: DetectedFace) -> QualityReport: ...

