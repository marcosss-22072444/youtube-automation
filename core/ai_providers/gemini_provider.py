"""
gemini_provider.py

Implementación concreta de TextAIProvider usando la API de Gemini.
Es la única clase del proyecto que conoce detalles específicos de Gemini.
"""

import google.generativeai as genai

from core.ai_providers.base import TextAIProvider
from core.config import settings
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)


class GeminiProvider(TextAIProvider):
    """Proveedor de IA de texto usando el modelo Gemini de Google."""

    def __init__(self, model_name: str | None = None):
       genai.configure(api_key=settings.gemini_api_key)
       self.model_name = model_name or settings.gemini_model
       self._model = genai.GenerativeModel(self.model_name)

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        try:
            model = self._model
            if system_instruction:
                # Gemini permite instrucción de sistema al crear el modelo
                model = genai.GenerativeModel(
                    self.model_name,
                    system_instruction=system_instruction,
                )

            response = model.generate_content(prompt)

            if not response.text:
                raise AIProviderError("Gemini devolvió una respuesta vacía.")

            return response.text

        except Exception as error:
            logger.error(f"Error al generar contenido con Gemini: {error}")
            raise AIProviderError(f"Fallo en GeminiProvider: {error}") from error