from __future__ import annotations

from fastapi import APIRouter, Depends

from ....core.config import Settings
from ..dependencies import get_app_settings

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("")
def config(settings: Settings = Depends(get_app_settings)) -> dict:
    return {
        "ai_provider": settings.ai_provider,
        "countries": settings.countries,
        "roles": settings.roles,
        "profile": settings.profile.model_dump(),
        "search": settings.search.model_dump(),
    }
