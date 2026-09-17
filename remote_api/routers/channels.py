"""channels.py — Endpoints REST de canales."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from channels import manager as channel_manager
from channels.exceptions import ChannelNotFoundError, DuplicateChannelNameError
from core.exceptions import ConfigError

router = APIRouter(prefix="/channels", tags=["channels"])


class ChannelCreate(BaseModel):
    name: str
    topic: str
    shorts_per_week: int = 0
    long_videos_per_week: int = 0
    voice_name: str = "ef_dora"


@router.get("")
def list_channels():
    channels = channel_manager.list_channels()
    return [{"id": c.id, "name": c.name, "topic": c.topic, "status": c.status} for c in channels]


@router.post("")
def create_channel(data: ChannelCreate):
    try:
        c = channel_manager.create_channel(
            data.name, data.topic, data.shorts_per_week, data.long_videos_per_week, data.voice_name
        )
        return {"id": c.id, "name": c.name}
    except (ConfigError, DuplicateChannelNameError) as error:
        raise HTTPException(status_code=400, detail=str(error))


@router.get("/{channel_id}")
def get_channel(channel_id: int):
    try:
        c = channel_manager.get_channel(channel_id)
        return {"id": c.id, "name": c.name, "topic": c.topic, "status": c.status, "voice_name": c.voice_name}
    except ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Canal no encontrado")

@router.post("/{channel_id}/pause")
def pause_channel(channel_id: int):
    try:
        c = channel_manager.pause_channel(channel_id)
        return {"id": c.id, "status": c.status}
    except ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Canal no encontrado")


@router.post("/{channel_id}/activate")
def activate_channel(channel_id: int):
    try:
        c = channel_manager.activate_channel(channel_id)
        return {"id": c.id, "status": c.status}
    except ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Canal no encontrado")


@router.delete("/{channel_id}")
def delete_channel(channel_id: int):
    try:
        channel_manager.delete_channel(channel_id)
        return {"deleted": channel_id}
    except ChannelNotFoundError:
        raise HTTPException(status_code=404, detail="Canal no encontrado")