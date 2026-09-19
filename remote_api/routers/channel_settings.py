"""channel_settings.py — Endpoints REST de ajustes por canal (channel_settings)."""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any

from channel_settings import manager as settings_manager

router = APIRouter(prefix="/channel-settings", tags=["channel_settings"])


class SettingSet(BaseModel):
    key: str
    value: Any


@router.get("/{channel_id}")
def list_settings(channel_id: int):
    return settings_manager.list_settings(channel_id)


@router.post("/{channel_id}")
def set_setting(channel_id: int, data: SettingSet):
    settings_manager.set_setting(channel_id, data.key, data.value)
    return {"channel_id": channel_id, "key": data.key, "status": "guardado"}


@router.delete("/{channel_id}/{key}")
def delete_setting(channel_id: int, key: str):
    settings_manager.delete_setting(channel_id, key)
    return {"channel_id": channel_id, "key": key, "status": "eliminado"}