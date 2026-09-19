"""schedules.py — Endpoints REST de horarios (channel_schedules)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from scheduler import manager as schedule_manager
from scheduler.exceptions import ScheduleEntryError

router = APIRouter(prefix="/schedules", tags=["schedules"])


class ScheduleCreate(BaseModel):
    channel_id: int
    content_type: str
    day_of_week: int
    time_of_day: str

class ScheduleUpdate(BaseModel):
    content_type: str
    day_of_week: int
    time_of_day: str
    enabled: bool = True


@router.get("/{channel_id}")
def list_schedule(channel_id: int):
    entries = schedule_manager.list_schedule_for_channel(channel_id)
    return [
        {"id": e.id, "content_type": e.content_type, "day_of_week": e.day_of_week,
         "time_of_day": e.time_of_day, "enabled": e.enabled}
        for e in entries
    ]


@router.post("")
def create_schedule(data: ScheduleCreate):
    try:
        e = schedule_manager.add_schedule_entry(data.channel_id, data.content_type, data.day_of_week, data.time_of_day)
        return {"id": e.id}
    except ScheduleEntryError as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.patch("/{entry_id}")
def update_schedule(entry_id: int, data: ScheduleUpdate):
    try:
        e = schedule_manager.update_schedule_entry(entry_id, data.content_type, data.day_of_week, data.time_of_day, data.enabled)
        if e is None:
            raise HTTPException(status_code=404, detail="Horario no encontrado")
        return {"id": e.id, "content_type": e.content_type, "day_of_week": e.day_of_week, "time_of_day": e.time_of_day, "enabled": e.enabled}
    except ScheduleEntryError as error:
        raise HTTPException(status_code=400, detail=str(error))

@router.delete("/{entry_id}")
def delete_schedule(entry_id: int):
    schedule_manager.remove_schedule_entry(entry_id)
    return {"deleted": entry_id}