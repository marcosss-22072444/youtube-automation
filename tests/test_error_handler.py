"""Test del Error Handler: fallo transitorio simulado, se recupera al 3er intento con backoff."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from core.constants import CONTENT_TYPE_SHORT
from channels import manager as channel_manager
from scheduler import manager as schedule_manager
from scheduler import repository as schedule_repository
from scheduler import runner as scheduler_runner
from scheduler.models import Job, STATUS_SUCCESS
import time


def test_error_handler_retries_and_recovers():
    initialize_database()

    attempts = {"count": 0}

    def _fake_execute_job(job: Job) -> None:
        attempts["count"] += 1
        if attempts["count"] < 3:
            schedule_repository.update_run_status(job.schedule_run_id, "failed", error_message="Connection timeout while calling external API")
        else:
            schedule_repository.update_run_status(job.schedule_run_id, STATUS_SUCCESS)

    scheduler_runner.execute_job = _fake_execute_job
    settings.error_handler["base_retry_delay_seconds"] = 1
    settings.error_handler["max_retry_delay_seconds"] = 3
    settings.scheduler["check_interval_seconds"] = 1

    canal = channel_manager.create_channel(name="Test Error Handler", topic="t", shorts_per_week=1, long_videos_per_week=0)
    tz = ZoneInfo(settings.scheduler["timezone"])
    target = datetime.now(tz) + timedelta(seconds=2)
    entry = schedule_manager.add_schedule_entry(canal.id, CONTENT_TYPE_SHORT, target.weekday(), target.strftime("%H:%M"))

    threads = scheduler_runner.start_scheduler()
    run_date = target.strftime("%Y-%m-%d")

    def _get_run():
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM schedule_runs WHERE schedule_entry_id=? AND run_date=?",
                (entry.id, run_date),
            ).fetchone()

    waited = 0
    run = None
    while waited < 30:
        run = _get_run()
        if run and run["status"] == STATUS_SUCCESS:
            break
        time.sleep(1)
        waited += 1

    scheduler_runner.stop_scheduler()
    for t in threads:
        t.join(timeout=3)

    assert run is not None
    assert run["status"] == STATUS_SUCCESS
    assert attempts["count"] == 3
    assert run["retry_count"] == 2