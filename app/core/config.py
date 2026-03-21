from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="FaceProof", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    secret_key: str = Field(default="change-me-before-production", alias="SECRET_KEY")
    session_cookie_name: str = Field(
        default="face_recognition_session", alias="SESSION_COOKIE_NAME"
    )

    database_url: str = Field(
        default="sqlite+pysqlite:///./data/face_recognition.db", alias="DATABASE_URL"
    )

    storage_backend: str = Field(default="local", alias="STORAGE_BACKEND")
    storage_bucket: str = Field(default="face-recognition", alias="STORAGE_BUCKET")
    storage_region: str = Field(default="us-east-1", alias="STORAGE_REGION")
    s3_endpoint_url: str | None = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_access_key: str | None = Field(default=None, alias="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, alias="S3_SECRET_KEY")
    s3_secure: bool = Field(default=False, alias="S3_SECURE")
    local_storage_path: str = Field(default="./data/storage", alias="LOCAL_STORAGE_PATH")

    recognition_backend: str = Field(default="demo", alias="RECOGNITION_BACKEND")
    onnx_model_path: str | None = Field(default=None, alias="ONNX_MODEL_PATH")
    onnx_input_size: int = Field(default=112, alias="ONNX_INPUT_SIZE")
    default_similarity_threshold: float = Field(
        default=0.86, alias="DEFAULT_SIMILARITY_THRESHOLD"
    )
    min_enrollment_captures: int = Field(default=3, alias="MIN_ENROLLMENT_CAPTURES")

    quality_min_brightness: float = Field(default=50, alias="QUALITY_MIN_BRIGHTNESS")
    quality_max_brightness: float = Field(default=220, alias="QUALITY_MAX_BRIGHTNESS")
    quality_min_blur: float = Field(default=75, alias="QUALITY_MIN_BLUR")
    quality_min_face_ratio: float = Field(default=0.08, alias="QUALITY_MIN_FACE_RATIO")

    bootstrap_operator_username: str = Field(
        default="admin", alias="BOOTSTRAP_OPERATOR_USERNAME"
    )
    bootstrap_operator_password: str = Field(
        default="Admin123!", alias="BOOTSTRAP_OPERATOR_PASSWORD"
    )
    bootstrap_operator_display_name: str = Field(
        default="System Admin", alias="BOOTSTRAP_OPERATOR_DISPLAY_NAME"
    )

    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    @property
    def local_storage_dir(self) -> Path:
        return (self.project_root / self.local_storage_path).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()
