from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.api.deps import SessionDep, AdminUser
from app.services.settings_service import SettingsService
from app.schemas.setting import SettingUpdate, SettingResponse

router = APIRouter()

@router.get("/", response_model=Dict[str, List[SettingResponse]], status_code=200)
def get_settings(db: SessionDep, admin: AdminUser):
    """Get all settings grouped by category"""
    svc = SettingsService(db)
    return svc.get_all_grouped()

@router.patch("/{key}")
def update_setting(key: str, payload: SettingUpdate, db: SessionDep, admin: AdminUser):
    """Update a specific setting"""
    svc = SettingsService(db)
    try:
        return svc.update(key, payload.value)
    except ValueError:
        raise HTTPException(status_code=404, detail="Setting not found")