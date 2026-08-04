"""
exceptions.py

Excepciones personalizadas del proyecto. Todas heredan de BaseAppError,
para poder capturar "cualquier error de nuestra app" de forma genérica
si hace falta, o capturar un tipo concreto si necesitamos reaccionar distinto.
"""


class BaseAppError(Exception):
    """Excepción base de la que heredan todas las demás del proyecto."""
    pass


class ConfigError(BaseAppError):
    """Se lanza cuando falta configuración necesaria (API key, valor mal escrito, etc.)."""
    pass


class AIProviderError(BaseAppError):
    """Se lanza cuando un proveedor de IA (Gemini, etc.) falla al generar contenido."""
    pass


class APIConnectionError(BaseAppError):
    """Se lanza cuando falla una conexión de red o a una API externa."""
    pass


class VoiceProviderError(BaseAppError):
    """Se lanza cuando un proveedor de voz (Kokoro, etc.) falla al generar audio."""
    pass


class ImageProviderError(BaseAppError):
    """Se lanza cuando un proveedor de imagen (FLUX, etc.) falla al generar una imagen."""
    pass