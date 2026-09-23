"""Test de recuperacion de franjas perdidas por PC apagado (9 casos)."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from channels import manager as channel_manager
from scheduler import manager as schedule_manager
from scheduler import runner as scheduler_runner
from scheduler.job_queue import queue_size, dequeue


def _insert_past_entry(channel_id, content_type, hours_ago):
    tz = ZoneInfo(settings.scheduler["timezone"])
    past = datetime.now(tz) - timedelta(hours=hours_ago)
    return schedule_manager.add_schedule_entry(channel_id, content_type, past.weekday(), past.strftime("%H:%M"))


def test_missed_schedule_recovery():
    initialize_database()
    c1 = channel_manager.create_channel(name="Test Recovery A", topic="t", shorts_per_week=1, long_videos_per_week=0)
    c2 = channel_manager.create_channel(name="Test Recovery B", topic="t", shorts_per_week=1, long_videos_per_week=0)
    c3 = channel_manager.create_channel(name="Test Recovery Paused", topic="t", shorts_per_week=1, long_videos_per_week=0)
    channel_manager.pause_channel(c3.id)

    e1 = _insert_past_entry(c1.id, "short", 3)
    e2 = _insert_past_entry(c1.id, "short", 5)
    e3 = _insert_past_entry(c1.id, "short", 20)
    e4 = _insert_past_entry(c2.id, "short", 2)
    e5 = _insert_past_entry(c3.id, "short", 2)

    scheduler_runner._recover_missed_entries()

    with get_connection() as conn:
        runs = conn.execute("SELECT * FROM schedule_runs").fetchall()
    by_entry = {r["schedule_entry_id"]: r for r in runs}

    assert e1.id in by_entry and e2.id in by_entry
    assert e3.id not in by_entry
    assert e4.id in by_entry
    assert e5.id not in by_entry
    assert all(by_entry[eid]["recovered"] == 1 for eid in (e1.id, e2.id, e4.id))

    scheduler_runner._recover_missed_entries()
    with get_connection() as conn:
        count_after = conn.execute("SELECT COUNT(*) c FROM schedule_runs").fetchone()["c"]
    assert count_after == len(runs)  # no duplica/re-reclama

    scheduler_runner._enqueue_pending_recovered()
    assert queue_size() == 2

    job_channels = set()
    while queue_size() > 0:
        j = dequeue(timeout=1)
        job_channels.add(j.channel_id)
    assert job_channels == {c1.id, c2.id}

    scheduler_runner._enqueue_pending_recovered()
    assert queue_size() == 1
