from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models import SystemSetting
from app.schemas.api import SystemInfoResponse
from app.services.recognition.engines import VerificationService


def build_system_info(
    db: Session, *, settings: Settings, verification_service: VerificationService
) -> SystemInfoResponse:
    threshold_row = db.get(SystemSetting, "default_similarity_threshold")
    captures_row = db.get(SystemSetting, "min_enrollment_captures")
    if settings.database_url.startswith("postgresql"):
        database_engine = "postgres"
    elif settings.database_url.startswith("sqlite"):
        database_engine = "sqlite"
    else:
        database_engine = "custom"

    return SystemInfoResponse(
        app_name=settings.app_name,
        app_env=settings.app_env,
        recognition_backend=verification_service.backend_name,
        model_name=verification_service.model_name,
        storage_backend=settings.storage_backend,
        default_similarity_threshold=float(threshold_row.value)
        if threshold_row is not None
        else settings.default_similarity_threshold,
        min_enrollment_captures=int(captures_row.value)
        if captures_row is not None
        else settings.min_enrollment_captures,
        database_engine=database_engine,
    )
