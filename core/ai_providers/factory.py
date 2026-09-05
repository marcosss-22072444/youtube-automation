"""
factory.py

Punto único de construcción de proveedores de IA de texto. Cualquier
módulo que necesite IA de texto debe usar get_text_provider_for_channel()
(si tiene contexto de canal) o get_default_text_provider() (sin
contexto de canal, ej: pruebas del Core) — así el fallback y las
credenciales por canal se aplican automáticamente en todo el proyecto.
"""

from core.ai_providers.base import TextAIProvider
from core.ai_providers.gemini_provider import GeminiProvider
from core.ai_providers.groq_provider import GroqProvider
from core.ai_providers.fallback_provider import FallbackProvider
from core.credentials.base import resolve_credential
from core.credentials.factory import get_default_credentials_store
from core.config import settings


def get_default_text_provider() -> TextAIProvider:
    """
    Devuelve el proveedor de IA de texto por defecto del proyecto,
    usando las claves globales de .env (sin contexto de canal):
    intenta Gemini primero, y si falla, cae automáticamente a Groq.
    """
    return FallbackProvider([GeminiProvider(), GroqProvider()])


def get_text_provider_for_channel(channel_id: int) -> TextAIProvider:
    from channel_settings import manager as settings_manager

    store = get_default_credentials_store()

    gemini_key = resolve_credential(channel_id, "gemini", settings.gemini_api_key, store)
    groq_key = resolve_credential(channel_id, "groq", settings.groq_api_key, store)
    gemini_model = settings_manager.get_setting(channel_id, "ai.gemini_model_override", default=settings.gemini_model)
    groq_model = settings_manager.get_setting(channel_id, "ai.groq_model_override", default=settings.groq_model)

    return FallbackProvider([
        GeminiProvider(api_key=gemini_key, model_name=gemini_model),
        GroqProvider(api_key=groq_key, model_name=groq_model),
    ])