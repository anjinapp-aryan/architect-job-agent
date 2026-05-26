"""Concrete SQLAlchemy implementations of the domain repository protocols."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...core.exceptions import DuplicateJobError, RepositoryError
from ...domain.entities import (
    Application,
    ApplicationStatus,
    CoverLetter,
    Job,
    Resume,
    SearchRun,
)
from .models import (
    ApplicationORM,
    CompanyORM,
    CoverLetterORM,
    JobORM,
    ResumeORM,
    SearchRunORM,
)


def _job_from_orm(o: JobORM) -> Job:
    return Job(
        id=o.id,
        fingerprint=o.fingerprint,
        title=o.title,
        company_name=o.company_name,
        location=o.location,
        country=o.country,
        source=o.source,
        salary=o.salary,
        url=o.url,
        description=o.description,
        date_posted=o.date_posted,
        search_timestamp=o.search_timestamp,
        is_remote=o.is_remote,
        match_score=o.match_score,
        scoring_breakdown=o.scoring_breakdown,
        strengths=o.strengths,
        gaps=o.gaps,
        recommendation=o.recommendation,
    )


class SQLJobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def _upsert_company(self, name: str) -> Optional[int]:
        if not name:
            return None
        existing = self.session.scalar(select(CompanyORM).where(CompanyORM.name == name))
        if existing:
            return existing.id
        company = CompanyORM(name=name)
        self.session.add(company)
        try:
            self.session.flush()
        except IntegrityError:
            self.session.rollback()
            existing = self.session.scalar(select(CompanyORM).where(CompanyORM.name == name))
            return existing.id if existing else None
        return company.id

    def add(self, job: Job) -> Job:
        company_id = self._upsert_company(job.company_name)
        orm = JobORM(
            fingerprint=job.fingerprint,
            title=job.title,
            company_name=job.company_name,
            company_id=company_id,
            location=job.location,
            country=job.country,
            source=job.source,
            salary=job.salary,
            url=job.url,
            description=job.description,
            date_posted=job.date_posted,
            search_timestamp=job.search_timestamp,
            is_remote=job.is_remote,
            match_score=job.match_score,
            scoring_breakdown=job.scoring_breakdown,
            strengths=job.strengths,
            gaps=job.gaps,
            recommendation=job.recommendation,
        )
        self.session.add(orm)
        try:
            self.session.flush()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateJobError(job.fingerprint) from exc
        return _job_from_orm(orm)

    def get(self, job_id: int) -> Optional[Job]:
        orm = self.session.get(JobORM, job_id)
        return _job_from_orm(orm) if orm else None

    def get_by_fingerprint(self, fingerprint: str) -> Optional[Job]:
        orm = self.session.scalar(select(JobORM).where(JobORM.fingerprint == fingerprint))
        return _job_from_orm(orm) if orm else None

    def list(
        self,
        country: Optional[str] = None,
        source: Optional[str] = None,
        min_score: Optional[int] = None,
        limit: int = 100,
    ) -> list[Job]:
        stmt = select(JobORM)
        if country:
            stmt = stmt.where(JobORM.country == country)
        if source:
            stmt = stmt.where(JobORM.source == source)
        if min_score is not None:
            stmt = stmt.where(JobORM.match_score >= min_score)
        stmt = stmt.order_by(JobORM.search_timestamp.desc()).limit(limit)
        return [_job_from_orm(o) for o in self.session.scalars(stmt)]

    def update_score(
        self,
        job_id: int,
        score: int,
        breakdown: dict,
        strengths: list[str],
        gaps: list[str],
        recommendation: str,
    ) -> None:
        orm = self.session.get(JobORM, job_id)
        if not orm:
            raise RepositoryError(f"Job {job_id} not found")
        orm.match_score = score
        orm.scoring_breakdown = breakdown
        orm.strengths = strengths
        orm.gaps = gaps
        orm.recommendation = recommendation

    def count(self) -> int:
        return int(self.session.scalar(select(func.count(JobORM.id))) or 0)

    def count_by_country(self) -> dict[str, int]:
        rows = self.session.execute(
            select(JobORM.country, func.count(JobORM.id)).group_by(JobORM.country)
        ).all()
        return {(r[0] or "Unknown"): int(r[1]) for r in rows}

    def count_by_role_keyword(self, roles: list[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for role in roles:
            pattern = f"%{role.lower()}%"
            count = self.session.scalar(
                select(func.count(JobORM.id)).where(func.lower(JobORM.title).like(pattern))
            )
            out[role] = int(count or 0)
        return out

    def count_high_scoring(self, threshold: int) -> int:
        return int(
            self.session.scalar(
                select(func.count(JobORM.id)).where(JobORM.match_score >= threshold)
            )
            or 0
        )


class SQLApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, application: Application) -> Application:
        orm = ApplicationORM(
            job_id=application.job_id,
            status=application.status.value,
            applied_at=application.applied_at,
            notes=application.notes,
            recruiter=application.recruiter,
            follow_up_at=application.follow_up_at,
        )
        self.session.add(orm)
        self.session.flush()
        application.id = orm.id
        return application

    def get(self, application_id: int) -> Optional[Application]:
        orm = self.session.get(ApplicationORM, application_id)
        return self._to_domain(orm) if orm else None

    def get_for_job(self, job_id: int) -> Optional[Application]:
        orm = self.session.scalar(
            select(ApplicationORM).where(ApplicationORM.job_id == job_id)
        )
        return self._to_domain(orm) if orm else None

    def list(self) -> list[Application]:
        orms = self.session.scalars(select(ApplicationORM).order_by(ApplicationORM.updated_at.desc()))
        return [self._to_domain(o) for o in orms]

    def update_status(
        self, application_id: int, status: ApplicationStatus, notes: Optional[str]
    ) -> Application:
        orm = self.session.get(ApplicationORM, application_id)
        if not orm:
            raise RepositoryError(f"Application {application_id} not found")
        orm.status = status.value
        if status == ApplicationStatus.APPLIED and not orm.applied_at:
            orm.applied_at = datetime.utcnow()
        if notes is not None:
            orm.notes = notes
        orm.updated_at = datetime.utcnow()
        self.session.flush()
        return self._to_domain(orm)

    def pipeline_counts(self) -> dict[str, int]:
        rows = self.session.execute(
            select(ApplicationORM.status, func.count(ApplicationORM.id)).group_by(
                ApplicationORM.status
            )
        ).all()
        return {r[0]: int(r[1]) for r in rows}

    @staticmethod
    def _to_domain(o: ApplicationORM) -> Application:
        return Application(
            id=o.id,
            job_id=o.job_id,
            status=ApplicationStatus(o.status),
            applied_at=o.applied_at,
            notes=o.notes,
            recruiter=o.recruiter,
            follow_up_at=o.follow_up_at,
            updated_at=o.updated_at,
        )


class SQLResumeRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, resume: Resume) -> Resume:
        orm = ResumeORM(
            label=resume.label,
            source_path=resume.source_path,
            parsed_text=resume.parsed_text,
            is_master=resume.is_master,
            job_id=resume.job_id,
        )
        self.session.add(orm)
        self.session.flush()
        resume.id = orm.id
        return resume

    def get(self, resume_id: int) -> Optional[Resume]:
        orm = self.session.get(ResumeORM, resume_id)
        return self._to_domain(orm) if orm else None

    def get_master(self) -> Optional[Resume]:
        orm = self.session.scalar(
            select(ResumeORM).where(ResumeORM.is_master.is_(True)).order_by(ResumeORM.created_at.desc())
        )
        return self._to_domain(orm) if orm else None

    def list_for_job(self, job_id: int) -> list[Resume]:
        return [
            self._to_domain(o)
            for o in self.session.scalars(select(ResumeORM).where(ResumeORM.job_id == job_id))
        ]

    @staticmethod
    def _to_domain(o: ResumeORM) -> Resume:
        return Resume(
            id=o.id,
            label=o.label,
            source_path=o.source_path,
            parsed_text=o.parsed_text,
            is_master=o.is_master,
            job_id=o.job_id,
            created_at=o.created_at,
        )


class SQLCoverLetterRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, letter: CoverLetter) -> CoverLetter:
        orm = CoverLetterORM(
            job_id=letter.job_id,
            content=letter.content,
            file_path=letter.file_path,
        )
        self.session.add(orm)
        self.session.flush()
        letter.id = orm.id
        return letter

    def list_for_job(self, job_id: int) -> list[CoverLetter]:
        orms = self.session.scalars(
            select(CoverLetterORM).where(CoverLetterORM.job_id == job_id)
        )
        return [
            CoverLetter(
                id=o.id, job_id=o.job_id, content=o.content,
                file_path=o.file_path, created_at=o.created_at,
            )
            for o in orms
        ]


class SQLSearchRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, run: SearchRun) -> SearchRun:
        orm = SearchRunORM(
            started_at=run.started_at,
            finished_at=run.finished_at,
            countries=list(run.countries),
            roles=list(run.roles),
            sources=list(run.sources),
            jobs_found=run.jobs_found,
            jobs_inserted=run.jobs_inserted,
            errors=list(run.errors),
        )
        self.session.add(orm)
        self.session.flush()
        run.id = orm.id
        return run

    def update(self, run: SearchRun) -> SearchRun:
        if run.id is None:
            return self.add(run)
        orm = self.session.get(SearchRunORM, run.id)
        if not orm:
            raise RepositoryError(f"SearchRun {run.id} not found")
        orm.finished_at = run.finished_at
        orm.jobs_found = run.jobs_found
        orm.jobs_inserted = run.jobs_inserted
        orm.errors = list(run.errors)
        return run

    def recent(self, limit: int = 10) -> list[SearchRun]:
        orms = self.session.scalars(
            select(SearchRunORM).order_by(SearchRunORM.started_at.desc()).limit(limit)
        )
        return [
            SearchRun(
                id=o.id,
                started_at=o.started_at,
                finished_at=o.finished_at,
                countries=o.countries or [],
                roles=o.roles or [],
                sources=o.sources or [],
                jobs_found=o.jobs_found,
                jobs_inserted=o.jobs_inserted,
                errors=o.errors or [],
            )
            for o in orms
        ]
