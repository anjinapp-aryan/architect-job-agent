import pytest

from architect_job_agent.core.exceptions import DuplicateJobError
from architect_job_agent.domain.entities import (
    Application,
    ApplicationStatus,
    Job,
)
from architect_job_agent.infrastructure.db.repositories import (
    SQLApplicationRepository,
    SQLJobRepository,
)


def _make_job(title="Architect", company="Acme", country="Germany"):
    fp = Job.make_fingerprint(title, company, country, "https://x.com/1")
    return Job(
        fingerprint=fp,
        title=title,
        company_name=company,
        country=country,
        location=country,
        source="linkedin",
        url="https://x.com/1",
        description="Build things.",
    )


def test_add_and_get_job(session):
    repo = SQLJobRepository(session)
    job = repo.add(_make_job())
    assert job.id is not None
    found = repo.get_by_fingerprint(job.fingerprint)
    assert found and found.title == "Architect"


def test_duplicate_job_raises(session):
    repo = SQLJobRepository(session)
    repo.add(_make_job())
    with pytest.raises(DuplicateJobError):
        repo.add(_make_job())


def test_score_update_and_high_scoring_count(session):
    repo = SQLJobRepository(session)
    job = repo.add(_make_job())
    repo.update_score(job.id, 92, {"skills": 90}, ["a"], ["b"], "Apply")
    assert repo.count_high_scoring(80) == 1
    assert repo.count_high_scoring(95) == 0


def test_application_pipeline(session):
    job_repo = SQLJobRepository(session)
    app_repo = SQLApplicationRepository(session)
    job = job_repo.add(_make_job())
    app_repo.add(Application(job_id=job.id, status=ApplicationStatus.SAVED))
    counts = app_repo.pipeline_counts()
    assert counts.get("Saved") == 1
