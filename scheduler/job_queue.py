"""
job_queue.py

Cola de trabajos en memoria, segura entre hilos (queue.Queue). El
ciclo de detección de franjas pendientes solo ENCOLA trabajos; uno o
varios workers los consumen de forma independiente. Empezamos con un
único worker (procesamiento secuencial, por la VRAM limitada de la
GPU), pero subir a varios workers en el futuro es solo cambiar
worker_count en config.yaml — esta cola ya lo soporta.
"""

import queue

from scheduler.models import Job

_job_queue: "queue.Queue[Job]" = queue.Queue()


def enqueue(job: Job) -> None:
    """Añade un trabajo a la cola."""
    _job_queue.put(job)


def dequeue(timeout: float | None = None) -> Job | None:
    """
    Retira el siguiente trabajo de la cola, esperando hasta timeout
    segundos si está vacía. Devuelve None si el timeout expira sin
    ningún trabajo disponible.
    """
    try:
        return _job_queue.get(timeout=timeout)
    except queue.Empty:
        return None


def queue_size() -> int:
    """Número de trabajos pendientes en la cola (para monitorización futura)."""
    return _job_queue.qsize()