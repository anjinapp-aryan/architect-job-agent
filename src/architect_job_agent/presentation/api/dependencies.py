"""FastAPI dependency wiring — pure constructor injection.

Every service receives its collaborators through ``Depends`` so request
handlers are easy to test and swap.
"""
from __future__ import annotations

from typing import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from ...application.services import (
    ApplicationTrackerService,
    CoverLetterService,
    DashboardService,
    JobScoringService,
    JobSearchService,
    ResumeService,
    ResumeTailoringService,
)
from ...core.config import Settings, get_settings
from ...infrastructure.ai.base import AIProvider
from ...infrastructure.ai.factory import build_ai_provider
from ...infrastructure.db.repositories import (
    SQLApplicationRepository,
    SQLCoverLetterRepository,
    SQLJobRepository,
    SQLResumeRepository,
    SQLSearchRunRepository,
)
from ...infrastructure.db.session import get_session_factory
from ...infrastructure.jobspy_client import JobSpyClient
from ...infrastructure.resume_parser import ResumeParser, ResumeWriter


def get_app_settings() -> Settings:
    return get_settings()


def get_db() -> Iterator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# --- repositories ---


def get_job_repo(session: Session = Depends(get_db)) -> SQLJobRepository:
    return SQLJobRepository(session)


def get_application_repo(session: Session = Depends(get_db)) -> SQLApplicationRepository:
    return SQLApplicationRepository(session)


def get_resume_repo(session: Session = Depends(get_db)) -> SQLResumeRepository:
    return SQLResumeRepository(session)


def get_letter_repo(session: Session = Depends(get_db)) -> SQLCoverLetterRepository:
    return SQLCoverLetterRepository(session)


def get_search_run_repo(session: Session = Depends(get_db)) -> SQLSearchRunRepository:
    return SQLSearchRunRepository(session)


# --- infra collaborators ---


def get_jobspy(settings: Settings = Depends(get_app_settings)) -> JobSpyClient:
    return JobSpyClient(
        results_wanted=settings.search.results_per_query,
        rate_limit_seconds=settings.search.rate_limit_seconds,
    )


def get_ai_provider() -> AIProvider:
    return build_ai_provider()


def get_resume_parser() -> ResumeParser:
    return ResumeParser()


def get_resume_writer() -> ResumeWriter:
    return ResumeWriter()


# --- services ---


def get_search_service(
    settings: Settings = Depends(get_app_settings),
    client: JobSpyClient = Depends(get_jobspy),
    job_repo: SQLJobRepository = Depends(get_job_repo),
    run_repo: SQLSearchRunRepository = Depends(get_search_run_repo),
) -> JobSearchService:
    return JobSearchService(settings, client, job_repo, run_repo)


def get_scoring_service(
    settings: Settings = Depends(get_app_settings),
    ai: AIProvider = Depends(get_ai_provider),
    job_repo: SQLJobRepository = Depends(get_job_repo),
) -> JobScoringService:
    return JobScoringService(settings, ai, job_repo)


def get_resume_service(
    settings: Settings = Depends(get_app_settings),
    parser: ResumeParser = Depends(get_resume_parser),
    writer: ResumeWriter = Depends(get_resume_writer),
    resume_repo: SQLResumeRepository = Depends(get_resume_repo),
) -> ResumeService:
    return ResumeService(settings, parser, writer, resume_repo)


def get_tailoring_service(
    settings: Settings = Depends(get_app_settings),
    ai: AIProvider = Depends(get_ai_provider),
    writer: ResumeWriter = Depends(get_resume_writer),
    resume_repo: SQLResumeRepository = Depends(get_resume_repo),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeTailoringService:
    return ResumeTailoringService(settings, ai, writer, resume_repo, resume_service)


def get_cover_letter_service(
    settings: Settings = Depends(get_app_settings),
    ai: AIProvider = Depends(get_ai_provider),
    letter_repo: SQLCoverLetterRepository = Depends(get_letter_repo),
    resume_service: ResumeService = Depends(get_resume_service),
) -> CoverLetterService:
    return CoverLetterService(settings, ai, letter_repo, resume_service)


def get_application_service(
    app_repo: SQLApplicationRepository = Depends(get_application_repo),
) -> ApplicationTrackerService:
    return ApplicationTrackerService(app_repo)


def get_dashboard_service(
    settings: Settings = Depends(get_app_settings),
    job_repo: SQLJobRepository = Depends(get_job_repo),
    app_repo: SQLApplicationRepository = Depends(get_application_repo),
    run_repo: SQLSearchRunRepository = Depends(get_search_run_repo),
) -> DashboardService:
    return DashboardService(settings, job_repo, app_repo, run_repo)
