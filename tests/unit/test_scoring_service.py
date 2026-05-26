from architect_job_agent.application.services import JobScoringService
from architect_job_agent.core.config import reload_settings
from architect_job_agent.domain.entities import Job
from architect_job_agent.infrastructure.ai.base import AIProvider
from architect_job_agent.infrastructure.db.repositories import SQLJobRepository


class FakeAI(AIProvider):
    name = "fake"

    def __init__(self):
        super().__init__(model="fake-1", temperature=0, max_tokens=10, timeout=1)

    def _complete(self, system, user):
        return (
            '{"match_score": 87, '
            '"scoring_breakdown": {"skills": 90, "experience": 85, '
            '"architecture": 88, "leadership": 80, "cloud": 92}, '
            '"strengths": ["AWS", "Architecture"], '
            '"gaps": ["Scala"], '
            '"recommendation": "Strong fit"}'
        )


def test_score_job_persists(session):
    settings = reload_settings()
    repo = SQLJobRepository(session)
    job = repo.add(
        Job(
            fingerprint="abc",
            title="Cloud Architect",
            company_name="Acme",
            country="Germany",
            source="linkedin",
            description="AWS, microservices, Terraform.",
        )
    )
    service = JobScoringService(settings, FakeAI(), repo)
    result = service.score_job(job)
    assert result.match_score == 87
    refreshed = repo.get(job.id)
    assert refreshed.match_score == 87
    assert "AWS" in (refreshed.strengths or [])
