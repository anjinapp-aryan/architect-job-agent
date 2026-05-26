from __future__ import annotations

from fastapi import APIRouter, Depends

from ....application.services import JobSearchService
from ....infrastructure.db.repositories import SQLSearchRunRepository
from ..dependencies import get_search_run_repo, get_search_service
from ..schemas import SearchRunOut, SearchTriggerIn

router = APIRouter(prefix="/api/search", tags=["search"])


@router.post("/run", response_model=SearchRunOut)
def trigger_search(
    payload: SearchTriggerIn | None = None,
    service: JobSearchService = Depends(get_search_service),
) -> SearchRunOut:
    payload = payload or SearchTriggerIn()
    run = service.run_full_search(countries=payload.countries, roles=payload.roles)
    return SearchRunOut(**run.model_dump())


@router.get("/runs", response_model=list[SearchRunOut])
def recent_runs(
    repo: SQLSearchRunRepository = Depends(get_search_run_repo),
) -> list[SearchRunOut]:
    return [SearchRunOut(**r.model_dump()) for r in repo.recent(20)]
