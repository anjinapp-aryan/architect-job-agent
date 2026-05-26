from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ....application.services import ApplicationTrackerService
from ....core.exceptions import RepositoryError
from ..dependencies import get_application_service
from ..schemas import ApplicationIn, ApplicationOut, ApplicationTransitionIn

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationOut])
def list_applications(
    service: ApplicationTrackerService = Depends(get_application_service),
) -> list[ApplicationOut]:
    return [ApplicationOut(**a.model_dump()) for a in service.list()]


@router.post("", response_model=ApplicationOut, status_code=201)
def create_application(
    payload: ApplicationIn,
    service: ApplicationTrackerService = Depends(get_application_service),
) -> ApplicationOut:
    app = service.create(payload.job_id, payload.status, payload.notes, payload.recruiter)
    return ApplicationOut(**app.model_dump())


@router.patch("/{application_id}", response_model=ApplicationOut)
def transition(
    application_id: int,
    payload: ApplicationTransitionIn,
    service: ApplicationTrackerService = Depends(get_application_service),
) -> ApplicationOut:
    try:
        app = service.transition(application_id, payload.status, payload.notes)
    except RepositoryError as exc:
        raise HTTPException(404, str(exc)) from exc
    return ApplicationOut(**app.model_dump())


@router.get("/pipeline")
def pipeline(
    service: ApplicationTrackerService = Depends(get_application_service),
) -> dict[str, int]:
    return service.pipeline()
