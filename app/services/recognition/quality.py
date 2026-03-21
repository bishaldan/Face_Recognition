import cv2
import numpy as np

from app.core.config import Settings
from app.services.recognition.base import DetectedFace, QualityReport


class BasicQualityAssessor:
    def __init__(self, settings: Settings):
        self.min_brightness = settings.quality_min_brightness
        self.max_brightness = settings.quality_max_brightness
        self.min_blur = settings.quality_min_blur
        self.min_face_ratio = settings.quality_min_face_ratio

    def assess(self, image: np.ndarray, face: DetectedFace) -> QualityReport:
        gray = cv2.cvtColor(face.crop, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        face_ratio = (face.bbox.width * face.bbox.height) / float(image.shape[0] * image.shape[1])

        reason_codes: list[str] = []
        if brightness < self.min_brightness or brightness > self.max_brightness:
            reason_codes.append("brightness_out_of_range")
        if blur < self.min_blur:
            reason_codes.append("too_blurry")
        if face_ratio < self.min_face_ratio:
            reason_codes.append("face_too_small")

        center_x = face.bbox.x + face.bbox.width / 2
        image_center_x = image.shape[1] / 2
        if abs(center_x - image_center_x) > image.shape[1] * 0.22:
            reason_codes.append("pose_off_center")

        score = max(
            0.0,
            min(
                1.0,
                (min(blur / max(self.min_blur, 1.0), 2.0) / 2.0)
                + (1.0 - min(abs(brightness - 128.0) / 128.0, 1.0)) * 0.35
                + min(face_ratio / max(self.min_face_ratio, 0.01), 1.0) * 0.15,
            ),
        )
        return QualityReport(
            accepted=not reason_codes,
            score=round(score, 3),
            reason_codes=reason_codes,
        )
