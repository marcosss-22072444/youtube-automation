"""main.py — TEST recuperacion de franjas perdidas."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from core.logger import get_logger
from core.schema import initialize_database
from core.database import get_connection
from core.config import settings
from channels import manager as channel_manager
from scheduler import manager as schedule_manager
from scheduler import repository as schedule_repository
from scheduler import runner as scheduler_runner
from scheduler.job_queue import queue_size, dequeue

logger = get_logger(__name__)

def _insert_past_entry(channel_id, content_type, hours_ago):
    tz = ZoneInfo(settings.scheduler["timezone"])
    past = datetime.now(tz) - timedelta(hours=hours_ago)
    e = schedule_manager.add_schedule_entry(channel_id, content_type, past.weekday(), past.strftime("%H:%M"))
    return e

def main():
    initialize_database()
    c1 = channel_manager.create_channel(name="Canal Recovery A", topic="t", shorts_per_week=1, long_videos_per_week=0)
    c2 = channel_manager.create_channel(name="Canal Recovery B", topic="t", shorts_per_week=1, long_videos_per_week=0)
    c3 = channel_manager.create_channel(name="Canal Recovery Paused", topic="t", shorts_per_week=1, long_videos_per_week=0)
    channel_manager.pause_channel(c3.id)

    e1 = _insert_past_entry(c1.id, "short", 3)   # dentro de ventana
    e2 = _insert_past_entry(c1.id, "short", 5)   # dentro de ventana, mismo canal+tipo
    e3 = _insert_past_entry(c1.id, "short", 20)  # fuera de ventana (12h)
    e4 = _insert_past_entry(c2.id, "short", 2)   # otro canal
    e5 = _insert_past_entry(c3.id, "short", 2)   # canal pausado

    scheduler_runner._recover_missed_entries()

    with get_connection() as conn:
        runs = conn.execute("SELECT * FROM schedule_runs").fetchall()
    runs_by_entry = {r["schedule_entry_id"]: r for r in runs}

    p1 = e1.id in runs_by_entry and e2.id in runs_by_entry
    logger.info(f"P1 ambas franjas dentro de ventana reclamadas (no se descartan): {p1}")

    p2 = e3.id not in runs_by_entry
    logger.info(f"P2 franja fuera de ventana NO reclamada: {p2}")

    p3 = e4.id in runs_by_entry
    logger.info(f"P3 canal aislado (c2) tambien reclamado: {p3}")

    p4 = e5.id not in runs_by_entry
    logger.info(f"P4 canal pausado NO reclamado: {p4}")

    p5 = all(runs_by_entry[eid]["recovered"] == 1 for eid in (e1.id, e2.id, e4.id))
    logger.info(f"P5 marcadas recovered=1: {p5}")

    # Segunda llamada a recovery: no debe duplicar ni re-reclamar
    scheduler_runner._recover_missed_entries()
    with get_connection() as conn:
        count_after = conn.execute("SELECT COUNT(*) c FROM schedule_runs").fetchone()["c"]
    p6 = count_after == len(runs)
    logger.info(f"P6 segunda llamada no duplica/re-reclama (test especifico pedido): {p6}")

    # Enqueue con limite: c1 tiene 2 recuperadas del mismo tipo, limite=1
    scheduler_runner._enqueue_pending_recovered()
    p7 = queue_size() == 2  # c1 (1 de 2, por limite) + c2 (1)
    logger.info(f"P7 limite por (channel,tipo) respetado al encolar (esperado 2 jobs): {p7} (queue_size={queue_size()})")

    job_channels = set()
    while queue_size() > 0:
        j = dequeue(timeout=1)
        job_channels.add(j.channel_id)
    p8 = job_channels == {c1.id, c2.id}
    logger.info(f"P8 jobs encolados de ambos canales, aislados: {p8}")

    # Ciclo siguiente: debe encolar la restante de c1
    scheduler_runner._enqueue_pending_recovered()
    p9 = queue_size() == 1
    logger.info(f"P9 franja restante se encola en el siguiente ciclo (no se pierde): {p9}")

    todas = all([p1, p2, p3, p4, p5, p6, p7, p8, p9])
    logger.info("✅ TODO CORRECTO" if todas else "❌ FALLOS")

if __name__ == "__main__":
    main()