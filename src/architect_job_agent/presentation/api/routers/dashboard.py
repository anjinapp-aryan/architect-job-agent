from __future__ import annotations

from fastapi import APIRouter, Depends

from ....application.services import DashboardService
from ..dependencies import get_dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def dashboard(service: DashboardService = Depends(get_dashboard_service)) -> dict:
    return service.summary()
