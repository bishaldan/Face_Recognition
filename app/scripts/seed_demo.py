from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import build_session_factory
from app.models import OperatorAccount
from app.services.bootstrap import ensure_bootstrap_state
from app.services.recognition.engines import VerificationService


def main() -> None:
    settings = get_settings()
    session_factory = build_session_factory(settings)
    verification_service = VerificationService(settings)
    with session_factory() as db:
        ensure_bootstrap_state(
            db,
            settings,
            backend_name=verification_service.backend_name,
            model_name=verification_service.model_name,
        )
        operator = db.scalar(
            select(OperatorAccount).where(
                OperatorAccount.username == settings.bootstrap_operator_username
            )
        )
        print(
            f"Operator ready: username={operator.username} display_name={operator.display_name}"
        )


if __name__ == "__main__":
    main()

