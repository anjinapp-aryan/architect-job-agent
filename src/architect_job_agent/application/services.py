"""Application-layer services (use cases).

Each service depends on repository protocols (domain.repositories) and the
AI provider abstraction, never on a concrete framework.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..core.config import Settings
from ..core.exceptions import (
    AIProviderError,
    CoverLetterGenerationError,
    DuplicateJobError,
    ResumeParsingError,
)
from ..core.logging import get_logger
from ..domain.entities import (
    Application,
    ApplicationStatus,
    CoverLetter,
    Job,
    Resume,
    ScoringResult,
    SearchRun,
)
from ..domain.repositories import (
    ApplicationRepository,
    CoverLetterRepository,
    JobRepository,
    ResumeRepository,
    SearchRunRepository,
)
from ..infrastructure.ai.base import AIProvider
from ..infrastructure.jobspy_client import JobSpyClient
from ..infrastructure.resume_parser import ResumeParser, ResumeWriter
from . import prompts

logger = get_logger(__name__)


# ----------------------------------------------------------------------
# Job search
# ----------------------------------------------------------------------


class JobSearchService:
    def __init__(
        self,
        settings: Settings,
        client: JobSpyClient,
        job_repo: JobRepository,
        run_repo: SearchRunRepository,
    ) -> None:
        self.settings = settings
        self.client = client
        self.job_repo = job_repo
        self.run_repo = run_repo

    def run_full_search(
        self,
        countries: Optional[list[str]] = None,
        roles: Optional[list[str]] = None,
    ) -> SearchRun:
        s = self.settings
        countries = countries or s.countries
        roles = roles or s.roles
        sources = s.search.sources

        run = SearchRun(
            started_at=datetime.utcnow(),
            countries=countries,
            roles=roles,
            sources=sources,
        )
        run = self.run_repo.add(run)

        found = 0
        inserted = 0
        errors: list[str] = []

        for country in countries:
            for role in roles:
                try:
                    jobs = self.client.search(
                        role=role,
                        country=country,
                        sources=sources,
                        max_age_days=s.search.max_age_days,
                        remote_allowed=s.search.remote_allowed,
                    )
                except Exception as exc:
                    msg = f"{country}/{role}: {exc}"
                    logger.error("search.country_role.failed", error=msg)
                    errors.append(msg)
                    continue

                found += len(jobs)
                for job in jobs:
                    if self.job_repo.get_by_fingerprint(job.fingerprint):
                        continue
                    try:
                        self.job_repo.add(job)
                        inserted += 1
                    except DuplicateJobError:
                        continue
                    except Exception as exc:
                        errors.append(f"persist: {exc}")

        run.finished_at = datetime.utcnow()
        run.jobs_found = found
        run.jobs_inserted = inserted
        run.errors = errors
        self.run_repo.update(run)
        logger.info("search.full.done", found=found, inserted=inserted, errors=len(errors))
        return run


# ----------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------


class JobScoringService:
    def __init__(
        self,
        settings: Settings,
        ai: AIProvider,
        job_repo: JobRepository,
    ) -> None:
        self.settings = settings
        self.ai = ai
        self.job_repo = job_repo

    def _profile_block(self) -> str:
        p = self.settings.profile
        return (
            f"Name: {p.full_name}\n"
            f"Title: {p.current_title}\n"
            f"Experience: {p.experience_years} years\n"
            f"Skills: {', '.join(p.skills)}\n"
            f"Preferred roles: {', '.join(p.preferred_roles)}\n"
            f"Preferred countries: {', '.join(p.preferred_countries)}\n"
            f"Summary: {p.summary}\n"
        )

    def score_job(self, job: Job) -> ScoringResult:
        user = prompts.SCORING_USER_TEMPLATE.format(
            profile=self._profile_block(),
            title=job.title,
            company=job.company_name,
            location=job.location or "",
            description=(job.description or "")[:6000],
        )
        try:
            raw = self.ai.generate_json(user, system=prompts.SCORING_SYSTEM)
        except AIProviderError as exc:
            logger.error("scoring.ai_failed", job_id=job.id, error=str(exc))
            raise

        score = int(max(0, min(100, raw.get("match_score", 0))))
        breakdown = {k: int(v) for k, v in (raw.get("scoring_breakdown") or {}).items()}
        result = ScoringResult(
            match_score=score,
            scoring_breakdown=breakdown,
            strengths=list(raw.get("strengths") or []),
            gaps=list(raw.get("gaps") or []),
            recommendation=str(raw.get("recommendation") or ""),
        )
        if job.id is not None:
            self.job_repo.update_score(
                job.id,
                result.match_score,
                result.scoring_breakdown,
                result.strengths,
                result.gaps,
                result.recommendation,
            )
        return result


# ----------------------------------------------------------------------
# Resume
# ----------------------------------------------------------------------


class ResumeService:
    def __init__(
        self,
        settings: Settings,
        parser: ResumeParser,
        writer: ResumeWriter,
        resume_repo: ResumeRepository,
    ) -> None:
        self.settings = settings
        self.parser = parser
        self.writer = writer
        self.resume_repo = resume_repo

    def ingest_master(self) -> Resume:
        path = Path(self.settings.resume.master_resume)
        text = self.parser.parse(path)
        resume = Resume(
            label="master",
            source_path=str(path),
            parsed_text=text,
            is_master=True,
        )
        return self.resume_repo.add(resume)

    def get_or_ingest_master(self) -> Resume:
        existing = self.resume_repo.get_master()
        if existing:
            return existing
        return self.ingest_master()


# ----------------------------------------------------------------------
# Tailoring
# ----------------------------------------------------------------------


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9]+")


def _safe_slug(text: str, max_len: int = 40) -> str:
    return _SAFE_NAME_RE.sub("-", text).strip("-")[:max_len] or "untitled"


class ResumeTailoringService:
    def __init__(
        self,
        settings: Settings,
        ai: AIProvider,
        writer: ResumeWriter,
        resume_repo: ResumeRepository,
        resume_service: ResumeService,
    ) -> None:
        self.settings = settings
        self.ai = ai
        self.writer = writer
        self.resume_repo = resume_repo
        self.resume_service = resume_service

    def tailor_for_job(self, job: Job) -> Resume:
        master = self.resume_service.get_or_ingest_master()
        user = prompts.TAILOR_USER_TEMPLATE.format(
            master_resume=master.parsed_text,
            title=job.title,
            company=job.company_name,
            description=(job.description or "")[:6000],
        )
        try:
            tailored_text = self.ai.generate(user, system=prompts.TAILOR_SYSTEM)
        except AIProviderError as exc:
            logger.error("tailor.ai_failed", job_id=job.id, error=str(exc))
            raise

        self._guardrail(master.parsed_text, tailored_text)

        out_dir = Path(self.settings.resume.tailored_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{_safe_slug(job.company_name)}_{_safe_slug(job.title)}_{uuid.uuid4().hex[:8]}.docx"
        out_path = out_dir / filename
        try:
            self.writer.write_docx(out_path, tailored_text)
        except ResumeParsingError as exc:
            logger.error("tailor.write_failed", error=str(exc))
            raise

        resume = Resume(
            label=f"tailored::{job.title}@{job.company_name}",
            source_path=str(out_path),
            parsed_text=tailored_text,
            is_master=False,
            job_id=job.id,
        )
        return self.resume_repo.add(resume)

    @staticmethod
    def _guardrail(master_text: str, tailored_text: str) -> None:
        """Best-effort anti-hallucination check: tailored output should not be
        wildly longer than the master, which would suggest invented content."""
        if len(tailored_text) > max(2000, int(len(master_text) * 1.5)):
            logger.warning(
                "tailor.guardrail.length_inflation",
                master_chars=len(master_text),
                tailored_chars=len(tailored_text),
            )


# ----------------------------------------------------------------------
# Cover letter
# ----------------------------------------------------------------------


class CoverLetterService:
    def __init__(
        self,
        settings: Settings,
        ai: AIProvider,
        letter_repo: CoverLetterRepository,
        resume_service: ResumeService,
    ) -> None:
        self.settings = settings
        self.ai = ai
        self.letter_repo = letter_repo
        self.resume_service = resume_service

    def generate(self, job: Job) -> CoverLetter:
        try:
            resume = self.resume_service.get_or_ingest_master()
        except ResumeParsingError as exc:
            raise CoverLetterGenerationError(f"Resume unavailable: {exc}") from exc

        profile = self.settings.profile
        user = prompts.COVER_LETTER_USER_TEMPLATE.format(
            profile=(
                f"{profile.full_name}, {profile.current_title}, "
                f"{profile.experience_years} yrs, skills: {', '.join(profile.skills)}"
            ),
            resume=resume.parsed_text[:5000],
            title=job.title,
            company=job.company_name,
            location=job.location or "",
            description=(job.description or "")[:4000],
            tone=self.settings.coverletter.default_tone,
            max_words=self.settings.coverletter.max_words,
        )
        try:
            content = self.ai.generate(user, system=prompts.COVER_LETTER_SYSTEM)
        except AIProviderError as exc:
            raise CoverLetterGenerationError(str(exc)) from exc

        out_dir = Path(self.settings.coverletter.output_directory)
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = (
            f"{_safe_slug(job.company_name)}_{_safe_slug(job.title)}_"
            f"{uuid.uuid4().hex[:8]}.txt"
        )
        out_path = out_dir / filename
        try:
            out_path.write_text(content, encoding="utf-8")
        except OSError as exc:
            raise CoverLetterGenerationError(f"Failed to write letter: {exc}") from exc

        letter = CoverLetter(job_id=job.id or 0, content=content, file_path=str(out_path))
        return self.letter_repo.add(letter)


# ----------------------------------------------------------------------
# Application tracking
# ----------------------------------------------------------------------


class ApplicationTrackerService:
    def __init__(self, repo: ApplicationRepository) -> None:
        self.repo = repo

    def create(self, job_id: int, status: ApplicationStatus = ApplicationStatus.NEW,
               notes: Optional[str] = None, recruiter: Optional[str] = None) -> Application:
        existing = self.repo.get_for_job(job_id)
        if existing:
            return existing
        app = Application(job_id=job_id, status=status, notes=notes, recruiter=recruiter)
        return self.repo.add(app)

    def transition(self, application_id: int, status: ApplicationStatus,
                   notes: Optional[str] = None) -> Application:
        return self.repo.update_status(application_id, status, notes)

    def list(self) -> list[Application]:
        return self.repo.list()

    def pipeline(self) -> dict[str, int]:
        out = {status.value: 0 for status in ApplicationStatus}
        out.update(self.repo.pipeline_counts())
        return out


# ----------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------


class DashboardService:
    def __init__(
        self,
        settings: Settings,
        job_repo: JobRepository,
        app_repo: ApplicationRepository,
        run_repo: SearchRunRepository,
    ) -> None:
        self.settings = settings
        self.job_repo = job_repo
        self.app_repo = app_repo
        self.run_repo = run_repo

    def summary(self) -> dict:
        threshold = self.settings.search.minimum_match_score
        return {
            "total_jobs": self.job_repo.count(),
            "jobs_by_country": self.job_repo.count_by_country(),
            "jobs_by_role": self.job_repo.count_by_role_keyword(self.settings.roles),
            "high_scoring_jobs": self.job_repo.count_high_scoring(threshold),
            "minimum_match_score": threshold,
            "application_pipeline": {
                **{s.value: 0 for s in ApplicationStatus},
                **self.app_repo.pipeline_counts(),
            },
            "recent_searches": [r.model_dump() for r in self.run_repo.recent(10)],
        }
