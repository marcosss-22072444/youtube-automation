"""
classifier.py

Decide si un error de un schedule_run merece reintentarse
automáticamente (RETRYABLE: fallos transitorios como red, timeouts,
límites de peticiones) o no (PERMANENT: errores de configuración,
credenciales, validación — reintentar no los arreglaría).
"""

RETRYABLE = "retryable"
PERMANENT = "permanent"

_RETRYABLE_PATTERNS = (
    "timeout", "timed out", "connection", "network",
    "429", "500", "502", "503", "504",
    "rate limit", "unavailable", "temporarily",
    "reset by peer", "read timed out",
)


def classify_error(error_message: str) -> str:
    """
    Clasifica un mensaje de error como RETRYABLE o PERMANENT, buscando
    patrones típicos de fallos transitorios en el texto del error.
    Por defecto (sin coincidencias), se considera PERMANENT — más
    seguro que reintentar indefinidamente algo que no se arreglará solo.
    """
    lower_message = error_message.lower()

    for pattern in _RETRYABLE_PATTERNS:
        if pattern in lower_message:
            return RETRYABLE

    return PERMANENT