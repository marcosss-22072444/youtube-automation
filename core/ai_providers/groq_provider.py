"""
groq_provider.py

Implementación concreta de TextAIProvider usando la API de Groq
(compatible con el SDK de OpenAI).
"""

from groq import Groq

from core.ai_providers.base import TextAIProvider
from core.config import settings
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)


class GroqProvider(TextAIProvider):
    """Proveedor de IA de texto usando modelos alojados en Groq."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.groq_model
        self._client = Groq(api_key=settings.groq_api_key)

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model_name,
                messages=messages,
            )
            content = response.choices[0].message.content

            if not content:
                raise AIProviderError("Groq devolvió una respuesta vacía.")

            return content

        except Exception as error:
            logger.error(f"Error al generar contenido con Groq: {error}")
            raise AIProviderError(f"Fallo en GroqProvider: {error}") from error