"""
factory.py

Punto único de construcción del proveedor de IA de texto por defecto
del proyecto. Cualquier módulo que necesite IA de texto debe usar
get_default_text_provider() en vez de instanciar un proveedor concreto
directamente — así el fallback (y cualquier cambio futuro de estrategia)
se aplica automáticamente en todo el proyecto.
"""

from core.ai_providers.base import TextAIProvider
from core.ai_providers.gemini_provider import GeminiProvider
from core.ai_providers.groq_provider import GroqProvider
from core.ai_providers.fallback_provider import FallbackProvider


def get_default_text_provider() -> TextAIProvider:
    """
    Devuelve el proveedor de IA de texto por defecto del proyecto:
    intenta Gemini primero, y si falla, cae automáticamente a Groq.
    """
    return FallbackProvider([GeminiProvider(), GroqProvider()])