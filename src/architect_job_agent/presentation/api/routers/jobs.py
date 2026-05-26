from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ....application.services import JobScoringService
from ....core.exceptions import AIProviderError
from ....infrastructure.db.repositories import SQLJobRepository
from ..dependencies import get_job_repo, get_scoring_service
from ..schemas import JobDetailOut, JobOut, ScoringOut

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    country: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    min_score: Optional[int] = Query(None, ge=0, le=100),
    limit: int = Query(100, le=500),
    repo: SQLJobRepository = Depends(get_job_repo),
) -> list[JobOut]:
    return [JobOut(**j.model_dump()) for j in repo.list(country, source, min_score, limit)]


@router.get("/{job_id}", response_model=JobDetailOut)
def get_job(job_id: int, repo: SQLJobRepository = Depends(get_job_repo)) -> JobDetailOut:
    job = repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return JobDetailOut(**job.model_dump())


@router.post("/{job_id}/score", response_model=ScoringOut)
def score_job(
    job_id: int,
    repo: SQLJobRepository = Depends(get_job_repo),
    service: JobScoringService = Depends(get_scoring_service),
) -> ScoringOut:
    job = repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    try:
        result = service.score_job(job)
    except AIProviderError as exc:
        raise HTTPException(503, f"AI provider error: {exc}") from exc
    return ScoringOut(**result.model_dump())
