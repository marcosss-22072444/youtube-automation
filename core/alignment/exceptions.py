"""exceptions.py — Excepciones del módulo de alineación forzada."""
from core.exceptions import BaseAppError

class AlignmentError(BaseAppError):
    """Se lanza cuando falla la alineación forzada de audio+texto."""
    pass