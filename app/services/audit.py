from sqlalchemy.orm import Session

from app.models import AuditLog


class AuditService:
    def record(
        self,
        db: Session,
        *,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict,
        operator_id: int | None,
    ) -> None:
        db.add(
            AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                operator_id=operator_id,
            )
        )

