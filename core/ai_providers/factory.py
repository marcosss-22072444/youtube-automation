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
    """
    Devuelve el proveedor de IA de texto para un canal concreto,
    usando sus credenciales propias si las tiene configuradas, o
    cayendo a las claves globales de .env si no (según
    config.yaml: credentials.allow_global_fallback).
    """
    store = get_default_credentials_store()

    gemini_key = resolve_credential(channel_id, "gemini", settings.gemini_api_key, store)
    groq_key = resolve_credential(channel_id, "groq", settings.groq_api_key, store)

    return FallbackProvider([
        GeminiProvider(api_key=gemini_key),
        GroqProvider(api_key=groq_key),
    ])