from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import OperatorAccount


class OperatorService:
    def authenticate(self, db: Session, username: str, password: str) -> OperatorAccount | None:
        operator = db.scalar(select(OperatorAccount).where(OperatorAccount.username == username))
        if operator is None or not operator.is_active:
            return None
        if not verify_password(password, operator.password_hash):
            return None
        operator.last_login_at = datetime.now(UTC)
        db.commit()
        return operator

