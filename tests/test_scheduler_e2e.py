"""Test end-to-end del Scheduler (mockeado, sin GPU/APIs): deteccion, idempotencia, cola, worker."""
from datetime import datetime
from zoneinfo import ZoneInfo

from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from core.constants import CONTENT_TYPE_SHORT
from channels import manager as channel_manager
from scheduler import manager as schedule_manager
from scheduler import runner as scheduler_runner
from scheduler.job_queue import dequeue, queue_size
from scheduler.models import Job, STATUS_SUCCESS


def _fake_execute_job(job: Job) -> None:
    from scheduler import repository as schedule_repository
    schedule_repository.update_run_status(job.schedule_run_id, STATUS_SUCCESS)


def _get_run_status(schedule_entry_id, run_date):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT status FROM schedule_runs WHERE schedule_entry_id=? AND run_date=?",
            (schedule_entry_id, run_date),
        ).fetchone()
    return row["status"] if row else None


def test_scheduler_detects_claims_and_processes():
    initialize_database()
    scheduler_runner.execute_job = _fake_execute_job

    canal = channel_manager.create_channel(name="Test Scheduler E2E", topic="t", shorts_per_week=1, long_videos_per_week=0)
    tz = ZoneInfo("Europe/Madrid")
    now = datetime.now(tz)
    entry = schedule_manager.add_schedule_entry(canal.id, CONTENT_TYPE_SHORT, now.weekday(), now.strftime("%H:%M"))

    scheduler_runner._detect_and_enqueue_due_entries()
    assert queue_size() == 1

    scheduler_runner._detect_and_enqueue_due_entries()
    assert queue_size() == 1  # idempotencia: no duplica

    job = dequeue(timeout=1)
    assert job is not None
    assert job.channel_id == canal.id
    assert job.content_type == CONTENT_TYPE_SHORT

    scheduler_runner.execute_job(job)
    run_date = now.strftime("%Y-%m-%d")
    assert _get_run_status(entry.id, run_date) == STATUS_SUCCESS
    assert queue_size() == 0