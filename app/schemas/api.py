from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentStartRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    notes: str | None = Field(default=None, max_length=2000)
    consent_given: bool


class EnrollmentCaptureRequest(BaseModel):
    image_data: str


class EnrollmentFinalizeRequest(BaseModel):
    session_id: int


class VerificationRequest(BaseModel):
    image_data: str
    candidate_user_id: int | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str | None
    notes: str | None
    is_active: bool
    enrollment_count: int
    created_at: datetime
    updated_at: datetime


class EnrollmentResponse(BaseModel):
    session_id: int
    status: str
    capture_count: int = 0
    accepted_count: int = 0
    message: str
    reason_codes: list[str] = Field(default_factory=list)
    quality_score: float | None = None


class VerificationResponse(BaseModel):
    status: str
    matched_user: UserResponse | None
    similarity_score: float | None
    threshold_used: float
    confidence_band: str
    reason_codes: list[str]
    quality_score: float | None
    backend_name: str
    model_name: str


class LogEntryResponse(BaseModel):
    id: int
    action: str
    entity_type: str
    entity_id: str
    details: dict
    created_at: datetime


class SettingUpdateRequest(BaseModel):
    default_similarity_threshold: float = Field(ge=0.0, le=1.0)
    min_enrollment_captures: int = Field(ge=1, le=10)


class SystemInfoResponse(BaseModel):
    app_name: str
    app_env: str
    recognition_backend: str
    model_name: str
    storage_backend: str
    default_similarity_threshold: float
    min_enrollment_captures: int
    database_engine: str
