"""FastAPI application factory."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ...core.config import get_settings
from ...core.exceptions import (
    AIProviderUnavailableError,
    ArchitectJobAgentError,
    ConfigError,
    JobSourceUnavailableError,
)
from ...core.logging import configure_logging, get_logger
from ...infrastructure.db.session import init_db
from .routers import (
    applications,
    config,
    cover_letters,
    dashboard,
    jobs,
    resumes,
    search,
)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.app.log_level)
    log = get_logger(__name__)

    app = FastAPI(
        title=settings.app.name,
        version="0.1.0",
        description="AI-powered international job search platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()
        log.info(
            "app.startup",
            provider=settings.ai_provider,
            db_host=settings.database_url.rsplit("@", 1)[-1].split("/")[0],
            auto_create_tables=settings.auto_create_tables,
        )

    @app.on_event("shutdown")
    def _shutdown() -> None:
        from ...infrastructure.db.session import dispose_engine
        dispose_engine()
        log.info("app.shutdown")

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(config.router)
    app.include_router(jobs.router)
    app.include_router(search.router)
    app.include_router(applications.router)
    app.include_router(resumes.router)
    app.include_router(cover_letters.router)
    app.include_router(dashboard.router)

    @app.exception_handler(ConfigError)
    async def _config_error(_: Request, exc: ConfigError):
        return JSONResponse({"detail": f"Configuration error: {exc}"}, status_code=500)

    @app.exception_handler(AIProviderUnavailableError)
    async def _ai_unavailable(_: Request, exc: AIProviderUnavailableError):
        return JSONResponse({"detail": f"AI provider unavailable: {exc}"}, status_code=503)

    @app.exception_handler(JobSourceUnavailableError)
    async def _source_unavailable(_: Request, exc: JobSourceUnavailableError):
        return JSONResponse({"detail": f"Job source unavailable: {exc}"}, status_code=503)

    @app.exception_handler(ArchitectJobAgentError)
    async def _generic(_: Request, exc: ArchitectJobAgentError):
        return JSONResponse({"detail": str(exc)}, status_code=500)

    return app


app = create_app()
