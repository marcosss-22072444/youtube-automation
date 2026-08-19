"""
exceptions.py

Excepciones específicas del módulo Scheduler.
"""

from core.exceptions import BaseAppError


class ScheduleEntryError(BaseAppError):
    """Se lanza cuando los datos de una franja de programación son inválidos."""
    pass


class PipelineExecutionError(BaseAppError):
    """Se lanza cuando falla la ejecución completa del pipeline para un trabajo."""
    pass