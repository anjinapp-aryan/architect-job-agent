from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ....application.services import CoverLetterService
from ....core.exceptions import CoverLetterGenerationError
from ....infrastructure.db.repositories import SQLCoverLetterRepository, SQLJobRepository
from ..dependencies import get_cover_letter_service, get_job_repo, get_letter_repo
from ..schemas import CoverLetterOut

router = APIRouter(prefix="/api/cover-letters", tags=["cover-letters"])


@router.post("/{job_id}", response_model=CoverLetterOut, status_code=201)
def generate(
    job_id: int,
    job_repo: SQLJobRepository = Depends(get_job_repo),
    service: CoverLetterService = Depends(get_cover_letter_service),
) -> CoverLetterOut:
    job = job_repo.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    try:
        letter = service.generate(job)
    except CoverLetterGenerationError as exc:
        raise HTTPException(503, str(exc)) from exc
    return CoverLetterOut(**letter.model_dump())


@router.get("/{job_id}", response_model=list[CoverLetterOut])
def list_for_job(
    job_id: int,
    repo: SQLCoverLetterRepository = Depends(get_letter_repo),
) -> list[CoverLetterOut]:
    return [CoverLetterOut(**c.model_dump()) for c in repo.list_for_job(job_id)]
