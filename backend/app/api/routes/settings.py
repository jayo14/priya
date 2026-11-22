"""Application settings and user notification preferences API endpoints."""

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import DbSession
from app.database.models.setting import AppSetting

router = APIRouter(prefix="/settings", tags=["Settings"])

PREFERENCES_KEY = "user_preferences"

DEFAULT_PREFERENCES = {
    "min_confidence_score": 60,
    "nigeria_only_filter": False,
    "telegram_notifications_enabled": True,
    "polling_interval_minutes": 5,
    "auto_verify_links": True,
    "theme": "dark",
}


class PreferencesResponse(BaseModel):
    min_confidence_score: int
    nigeria_only_filter: bool
    telegram_notifications_enabled: bool
    polling_interval_minutes: int
    auto_verify_links: bool
    theme: str


class PreferencesUpdateRequest(BaseModel):
    min_confidence_score: Optional[int] = Field(None, ge=0, le=100)
    nigeria_only_filter: Optional[bool] = None
    telegram_notifications_enabled: Optional[bool] = None
    polling_interval_minutes: Optional[int] = Field(None, ge=1, le=60)
    auto_verify_links: Optional[bool] = None
    theme: Optional[str] = None


def _get_or_create_preferences(db: Session) -> AppSetting:
    setting = (
        db.execute(select(AppSetting).where(AppSetting.key == PREFERENCES_KEY)).scalar_one_or_none()
    )
    if not setting:
        setting = AppSetting(
            key=PREFERENCES_KEY,
            value=DEFAULT_PREFERENCES,
            description="User application and deal discovery preferences",
        )
        db.add(setting)
        db.commit()
        db.refresh(setting)
    return setting


@router.get("", response_model=PreferencesResponse)
def get_settings(db: Session = DbSession):
    """Retrieve user preferences and discovery configurations."""
    setting = _get_or_create_preferences(db)
    val = dict(DEFAULT_PREFERENCES)
    val.update(setting.value or {})
    return PreferencesResponse(**val)


@router.patch("", response_model=PreferencesResponse)
def update_settings(updates: PreferencesUpdateRequest, db: Session = DbSession):
    """Update user preferences and notification thresholds."""
    setting = _get_or_create_preferences(db)
    current_val = dict(DEFAULT_PREFERENCES)
    current_val.update(setting.value or {})

    # Apply non-null updates
    update_data = updates.model_dump(exclude_unset=True)
    current_val.update(update_data)

    setting.value = current_val
    db.commit()
    db.refresh(setting)

    return PreferencesResponse(**current_val)
