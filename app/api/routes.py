from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_db, require_operator
from app.models import (
    AuditLog,
    EnrollmentImage,
    EnrollmentSession,
    FaceEmbedding,
    OperatorAccount,
    SystemSetting,
    User,
    VerificationAttempt,
)
from app.schemas.api import (
    EnrollmentCaptureRequest,
    EnrollmentFinalizeRequest,
    EnrollmentResponse,
    EnrollmentStartRequest,
    LogEntryResponse,
    SettingUpdateRequest,
    SystemInfoResponse,
    UserResponse,
    VerificationRequest,
    VerificationResponse,
)
from app.services.audit import AuditService
from app.services.operators import OperatorService
from app.services.recognition.engines import decode_data_url
from app.services.system_info import build_system_info

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def _template_context(request: Request, **kwargs):
    return {
        "request": request,
        "settings": request.app.state.settings,
        "operator": kwargs.pop("operator", None),
        **kwargs,
    }


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db), operator: OperatorAccount = Depends(require_operator)):
    user_count = db.scalar(select(func.count(User.id))) or 0
    active_user_count = db.scalar(select(func.count(User.id)).where(User.is_active.is_(True))) or 0
    verification_count = db.scalar(select(func.count(VerificationAttempt.id))) or 0
    recent_attempts = list(
        db.scalars(
            select(VerificationAttempt)
            .options(selectinload(VerificationAttempt.matched_user))
            .order_by(desc(VerificationAttempt.created_at))
            .limit(8)
        )
    )
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        _template_context(
            request,
            operator=operator,
            stats={
                "user_count": user_count,
                "active_user_count": active_user_count,
                "verification_count": verification_count,
            },
            recent_attempts=recent_attempts,
            system_info=build_system_info(
                db,
                settings=request.app.state.settings,
                verification_service=request.app.state.verification_service,
            ),
        ),
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    if request.session.get("operator_id"):
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(request, "login.html", _template_context(request))


@router.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    operator = OperatorService().authenticate(db, username, password)
    if operator is None:
        return templates.TemplateResponse(
            request,
            "login.html",
            _template_context(request, error="Username or password was not recognized."),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    request.session["operator_id"] = operator.id
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/enroll", response_class=HTMLResponse)
def enroll_page(request: Request, operator: OperatorAccount = Depends(require_operator)):
    return templates.TemplateResponse(
        request,
        "enroll.html",
        _template_context(
            request,
            operator=operator,
            min_enrollment_captures=request.app.state.settings.min_enrollment_captures,
        ),
    )


@router.get("/verify", response_class=HTMLResponse)
def verify_page(
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    users = list(db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.full_name)))
    return templates.TemplateResponse(
        request,
        "verify.html",
        _template_context(request, operator=operator, users=users),
    )


@router.get("/users", response_class=HTMLResponse)
def users_page(
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    users = list(
        db.scalars(
            select(User)
            .order_by(User.is_active.desc(), User.full_name.asc())
            .options(selectinload(User.embeddings))
        )
    )
    return templates.TemplateResponse(
        request,
        "users.html",
        _template_context(request, operator=operator, users=users),
    )


@router.get("/users/{user_id}", response_class=HTMLResponse)
def user_detail_page(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    user = db.scalar(
        select(User).where(User.id == user_id).options(selectinload(User.embeddings))
    )
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    images = list(
        db.scalars(
            select(EnrollmentImage)
            .join(EnrollmentSession, EnrollmentSession.id == EnrollmentImage.session_id)
            .where(EnrollmentSession.finalized_user_id == user_id)
            .order_by(EnrollmentImage.created_at.desc())
        )
    )
    return templates.TemplateResponse(
        request,
        "user_detail.html",
        _template_context(request, operator=operator, user=user, images=images),
    )


@router.get("/logs", response_class=HTMLResponse)
def logs_page(
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    logs = list(db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(100)))
    verifications = list(
        db.scalars(
            select(VerificationAttempt)
            .options(selectinload(VerificationAttempt.matched_user))
            .order_by(desc(VerificationAttempt.created_at))
            .limit(50)
        )
    )
    return templates.TemplateResponse(
        request,
        "logs.html",
        _template_context(request, operator=operator, logs=logs, verifications=verifications),
    )


@router.get("/settings", response_class=HTMLResponse)
def settings_page(
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    settings_rows = {item.key: item.value for item in db.scalars(select(SystemSetting))}
    return templates.TemplateResponse(
        request,
        "settings.html",
        _template_context(
            request,
            operator=operator,
            system_settings=settings_rows,
            system_info=build_system_info(
                db,
                settings=request.app.state.settings,
                verification_service=request.app.state.verification_service,
            ),
        ),
    )


@router.post("/settings")
def update_settings_page(
    request: Request,
    default_similarity_threshold: float = Form(...),
    min_enrollment_captures: int = Form(...),
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    payload = SettingUpdateRequest(
        default_similarity_threshold=default_similarity_threshold,
        min_enrollment_captures=min_enrollment_captures,
    )
    for key, value in {
        "default_similarity_threshold": str(payload.default_similarity_threshold),
        "min_enrollment_captures": str(payload.min_enrollment_captures),
    }.items():
        row = db.get(SystemSetting, key)
        if row is not None:
            row.value = value
    AuditService().record(
        db,
        action="settings.updated",
        entity_type="system_setting",
        entity_id="global",
        details=payload.model_dump(),
        operator_id=operator.id,
    )
    db.commit()
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/media/{object_key:path}")
def media_proxy(
    object_key: str,
    request: Request,
    operator: OperatorAccount = Depends(require_operator),
):
    _ = operator
    content = request.app.state.storage_service.fetch_bytes(object_key)
    return StreamingResponse(iter([content]), media_type="image/jpeg")


@router.post("/api/enrollments/start", response_model=EnrollmentResponse)
def start_enrollment(
    payload: EnrollmentStartRequest,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    if not payload.consent_given:
        raise HTTPException(status_code=400, detail="Consent is required before enrollment.")
    session = EnrollmentSession(
        requested_name=payload.full_name,
        requested_email=payload.email,
        notes=payload.notes,
        consent_given=payload.consent_given,
        status="capturing",
        operator_id=operator.id,
    )
    db.add(session)
    db.flush()
    AuditService().record(
        db,
        action="enrollment.started",
        entity_type="enrollment_session",
        entity_id=str(session.id),
        details={"requested_name": payload.full_name},
        operator_id=operator.id,
    )
    db.commit()
    return EnrollmentResponse(
        session_id=session.id,
        status=session.status,
        message="Enrollment session started. Capture clear photos one at a time.",
    )


@router.post("/api/enrollments/{session_id}/captures", response_model=EnrollmentResponse)
def add_enrollment_capture(
    session_id: int,
    payload: EnrollmentCaptureRequest,
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    session = db.get(EnrollmentSession, session_id)
    if session is None or session.status not in {"capturing", "pending"}:
        raise HTTPException(status_code=404, detail="Enrollment session not available.")

    image_bytes = decode_data_url(payload.image_data)
    verification_service = request.app.state.verification_service
    processed = verification_service.pipeline.process_image(
        image_bytes, verification_service.current_threshold(db)
    )

    capture_count = (
        db.scalar(
            select(func.count(EnrollmentImage.id)).where(EnrollmentImage.session_id == session_id)
        )
        or 0
    )
    object_key = f"enrollments/{session_id}/capture_{capture_count + 1}.jpg"
    request.app.state.storage_service.store_image(
        object_key=object_key, content=image_bytes, content_type="image/jpeg"
    )

    accepted = processed.embedding is not None
    image_row = EnrollmentImage(
        session_id=session_id,
        object_key=object_key,
        capture_index=int(capture_count + 1),
        quality_score=processed.quality_score or 0.0,
        reason_codes=processed.reason_codes,
        accepted=accepted,
    )
    db.add(image_row)
    db.flush()

    if accepted and processed.embedding is not None:
        db.add(
            FaceEmbedding(
                session_id=session_id,
                enrollment_image_id=image_row.id,
                backend_name=processed.backend_name,
                model_name=processed.model_name,
                vector=processed.embedding,
            )
        )

    AuditService().record(
        db,
        action="enrollment.capture_added",
        entity_type="enrollment_session",
        entity_id=str(session_id),
        details={"accepted": accepted, "reason_codes": processed.reason_codes},
        operator_id=operator.id,
    )
    db.commit()

    accepted_count = (
        db.scalar(
            select(func.count(EnrollmentImage.id)).where(
                EnrollmentImage.session_id == session_id,
                EnrollmentImage.accepted.is_(True),
            )
        )
        or 0
    )
    return EnrollmentResponse(
        session_id=session_id,
        status=session.status,
        capture_count=int(capture_count + 1),
        accepted_count=int(accepted_count),
        message="Capture accepted." if accepted else "Capture saved, but it needs another try.",
        reason_codes=processed.reason_codes,
        quality_score=processed.quality_score,
    )


@router.post("/api/enrollments/{session_id}/finalize", response_model=UserResponse)
def finalize_enrollment(
    session_id: int,
    payload: EnrollmentFinalizeRequest,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    if payload.session_id != session_id:
        raise HTTPException(status_code=400, detail="Session mismatch.")
    session = db.get(EnrollmentSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Enrollment session not found.")

    accepted_images = list(
        db.scalars(
            select(EnrollmentImage)
            .where(EnrollmentImage.session_id == session_id, EnrollmentImage.accepted.is_(True))
            .order_by(EnrollmentImage.capture_index.asc())
        )
    )
    min_captures_row = db.get(SystemSetting, "min_enrollment_captures")
    min_captures = int(min_captures_row.value) if min_captures_row is not None else 3
    if len(accepted_images) < min_captures:
        raise HTTPException(
            status_code=400,
            detail=f"At least {min_captures} accepted captures are required.",
        )

    user = User(
        full_name=session.requested_name,
        email=session.requested_email,
        notes=session.notes,
        enrollment_count=len(accepted_images),
    )
    db.add(user)
    db.flush()

    pending_embeddings = list(
        db.scalars(select(FaceEmbedding).where(FaceEmbedding.session_id == session_id))
    )
    for embedding in pending_embeddings:
        embedding.user_id = user.id

    session.status = "finalized"
    session.finalized_user_id = user.id
    AuditService().record(
        db,
        action="enrollment.finalized",
        entity_type="user",
        entity_id=str(user.id),
        details={"session_id": session_id, "capture_count": len(accepted_images)},
        operator_id=operator.id,
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post("/api/verifications", response_model=VerificationResponse)
def create_verification(
    payload: VerificationRequest,
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    image_bytes = decode_data_url(payload.image_data)
    service = request.app.state.verification_service
    result, matched_user = service.verify(
        db, image_bytes=image_bytes, candidate_user_id=payload.candidate_user_id
    )
    attempt = VerificationAttempt(
        matched_user_id=matched_user.id if matched_user else None,
        operator_id=operator.id,
        status=result.status,
        similarity_score=result.similarity_score,
        threshold_used=result.threshold_used,
        confidence_band=result.confidence_band,
        reason_codes=result.reason_codes,
        backend_name=result.backend_name,
        model_name=result.model_name,
        quality_score=result.quality_score,
    )
    db.add(attempt)
    db.flush()
    AuditService().record(
        db,
        action="verification.created",
        entity_type="verification_attempt",
        entity_id=str(attempt.id),
        details={
            "status": result.status,
            "matched_user_id": matched_user.id if matched_user else None,
            "reason_codes": result.reason_codes,
        },
        operator_id=operator.id,
    )
    db.commit()
    if matched_user:
        db.refresh(matched_user)
    return VerificationResponse(
        status=result.status,
        matched_user=UserResponse.model_validate(matched_user) if matched_user else None,
        similarity_score=result.similarity_score,
        threshold_used=result.threshold_used,
        confidence_band=result.confidence_band,
        reason_codes=result.reason_codes,
        quality_score=result.quality_score,
        backend_name=result.backend_name,
        model_name=result.model_name,
    )


@router.get("/api/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db), operator: OperatorAccount = Depends(require_operator)
):
    _ = operator
    users = list(db.scalars(select(User).order_by(User.full_name.asc())))
    return [UserResponse.model_validate(user) for user in users]


@router.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    _ = operator
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return UserResponse.model_validate(user)


@router.post("/api/users/{user_id}/disable", response_model=UserResponse)
def disable_user(
    user_id: int,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = False
    AuditService().record(
        db,
        action="user.disabled",
        entity_type="user",
        entity_id=str(user_id),
        details={"disabled_by": operator.username},
        operator_id=operator.id,
    )
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/api/logs", response_model=list[LogEntryResponse])
def list_logs(
    db: Session = Depends(get_db), operator: OperatorAccount = Depends(require_operator)
):
    _ = operator
    logs = list(db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(200)))
    return [
        LogEntryResponse(
            id=log.id,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            details=log.details,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/api/system/info", response_model=SystemInfoResponse)
def system_info(
    request: Request,
    db: Session = Depends(get_db),
    operator: OperatorAccount = Depends(require_operator),
):
    _ = operator
    return build_system_info(
        db,
        settings=request.app.state.settings,
        verification_service=request.app.state.verification_service,
    )


@router.get("/health")
def health(request: Request):
    return {
        "status": "ok",
        "app": request.app.state.settings.app_name,
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/ready")
def ready(request: Request):
    db = request.app.state.session_factory()
    try:
        db.execute(select(1))
        if request.app.state.settings.recognition_backend == "onnx" and not request.app.state.settings.onnx_model_path:
            raise HTTPException(status_code=503, detail="ONNX backend selected but no model path configured.")
        request.app.state.storage_service.initialize()
    finally:
        db.close()
    return {"status": "ready"}
