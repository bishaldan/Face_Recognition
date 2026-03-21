from collections.abc import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.models import OperatorAccount


def get_db(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def get_runtime_settings() -> Settings:
    return get_settings()


def require_operator(request: Request, db: Session = Depends(get_db)) -> OperatorAccount:
    operator_id = request.session.get("operator_id")
    if not operator_id:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    operator = db.get(OperatorAccount, operator_id)
    if operator is None or not operator.is_active:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return operator
