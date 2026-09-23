"""Aislamiento entre tests: limpia la cola y detiene cualquier hilo del scheduler antes/despues de cada test."""
import pytest
from scheduler import job_queue as job_queue_module
from scheduler import runner as scheduler_runner


@pytest.fixture(autouse=True)
def _reset_scheduler_state():
    scheduler_runner.stop_scheduler()
    while job_queue_module.queue_size() > 0:
        job_queue_module.dequeue(timeout=0.1)
    yield
    scheduler_runner.stop_scheduler()