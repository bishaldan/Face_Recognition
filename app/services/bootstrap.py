from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models import ModelVersion, OperatorAccount, SystemSetting


def ensure_bootstrap_state(db: Session, settings: Settings, *, backend_name: str, model_name: str) -> None:
    operator = db.scalar(
        select(OperatorAccount).where(
            OperatorAccount.username == settings.bootstrap_operator_username
        )
    )
    if operator is None:
        db.add(
            OperatorAccount(
                username=settings.bootstrap_operator_username,
                display_name=settings.bootstrap_operator_display_name,
                password_hash=hash_password(settings.bootstrap_operator_password),
            )
        )

    setting_defaults = {
        "default_similarity_threshold": (
            str(settings.default_similarity_threshold),
            "Similarity score threshold used for verification decisions.",
        ),
        "min_enrollment_captures": (
            str(settings.min_enrollment_captures),
            "Minimum accepted enrollment captures required before finalizing a user.",
        ),
    }
    for key, (value, description) in setting_defaults.items():
        current = db.get(SystemSetting, key)
        if current is None:
            db.add(SystemSetting(key=key, value=value, description=description))

    existing_model = db.scalar(
        select(ModelVersion).where(
            ModelVersion.backend_name == backend_name,
            ModelVersion.model_name == model_name,
            ModelVersion.is_active.is_(True),
        )
    )
    if existing_model is None:
        db.add(
            ModelVersion(
                backend_name=backend_name,
                model_name=model_name,
                version_label="v0.1.0",
                is_active=True,
            )
        )

    db.commit()

