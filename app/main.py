from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import new_request_id
from app.db.base import Base
from app.db.session import build_engine, get_db_factory
from app.services.bootstrap import ensure_bootstrap_state
from app.services.recognition.engines import VerificationService
from app.services.storage.base import LocalStorageService, MemoryStorageService
from app.services.storage.s3 import S3StorageService


def build_storage_service(settings):
    if settings.storage_backend == "s3":
        return S3StorageService(settings)
    if settings.storage_backend == "memory":
        return MemoryStorageService()
    return LocalStorageService(settings.local_storage_dir)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    storage_service = app.state.storage_service
    storage_service.initialize()

    engine = build_engine(settings)
    Base.metadata.create_all(bind=engine)
    db = app.state.session_factory()
    try:
        ensure_bootstrap_state(
            db,
            settings,
            backend_name=app.state.verification_service.backend_name,
            model_name=app.state.verification_service.model_name,
        )
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        session_cookie=settings.session_cookie_name,
        same_site="lax",
        https_only=False,
    )
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    _, session_factory = get_db_factory(settings)
    app.state.settings = settings
    app.state.session_factory = session_factory
    app.state.storage_service = build_storage_service(settings)
    app.state.verification_service = VerificationService(settings)

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request.state.request_id = new_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred.",
                "request_id": getattr(request.state, "request_id", "unknown"),
            },
        )

    app.include_router(router)
    return app


app = create_app()
