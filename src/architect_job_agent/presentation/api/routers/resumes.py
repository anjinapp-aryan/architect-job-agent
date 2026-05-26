from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ....application.services import ResumeService, ResumeTailoringService
from ....core.exceptions import AIProviderError, ResumeParsingError
from ....infrastructure.db.repositories import SQLJobRepository
from ..dependencies import (
    get_job_repo,
    get_resume_service,
    get_tailoring_service,
)
from ..schemas import ResumeOut

router = APIRouter(prefix="/api/resumes", tags=["resumes"])


@router.post("/master/ingest", response_model=ResumeOut, status_code=201)
def ingest_master(service: ResumeService = Depends(get_resume_service)) -> ResumeOut:
    try:
        resume = service.ingest_master()
    except ResumeParsingError as exc:
        raise HTTPException(422, str(exc)) from exc
    return ResumeOut(**resume.model_dump(exclude={"parsed_text"}))


@router.post("/tailor/{job_id}", response_model=ResumeOut, status_code=201)
def tailor(
    job_id: int,
    job_repo: SQLJobRepository = Depends(get_job_repo),
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> ResumeOut:
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    try:
        resume = service.tailor_for_job(job)
    except (AIProviderError, ResumeParsingError) as exc:
        raise HTTPException(503, str(exc)) from exc
    return ResumeOut(**resume.model_dump(exclude={"parsed_text"}))
