import numpy as np

from app.core.config import Settings
from app.services.recognition.base import BoundingBox, DetectedFace
from app.services.recognition.quality import BasicQualityAssessor


def test_quality_accepts_balanced_face_crop():
    assessor = BasicQualityAssessor(Settings())
    image = np.full((300, 300, 3), 140, dtype=np.uint8)
    image[100:220, 100:220] = 90
    image[120:130, 120:200] = 220
    image[160:170, 120:200] = 35
    image[185:195, 135:185] = 210
    face = DetectedFace(
        bbox=BoundingBox(x=90, y=90, width=130, height=130),
        crop=image[90:220, 90:220],
    )
    report = assessor.assess(image, face)
    assert report.accepted
    assert report.score > 0


def test_quality_rejects_dark_small_face():
    assessor = BasicQualityAssessor(Settings())
    image = np.zeros((300, 300, 3), dtype=np.uint8)
    face = DetectedFace(
        bbox=BoundingBox(x=0, y=0, width=20, height=20),
        crop=image[:20, :20],
    )
    report = assessor.assess(image, face)
    assert not report.accepted
    assert "face_too_small" in report.reason_codes
