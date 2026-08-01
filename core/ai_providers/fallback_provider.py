"""
fallback_provider.py

Proveedor de IA "compuesto": prueba una lista de proveedores en orden,
usando el primero que responda con éxito. Si todos fallan, relanza el
último error. Transparente para el resto del proyecto: se comporta
como un TextAIProvider más.
"""

from core.ai_providers.base import TextAIProvider
from core.exceptions import AIProviderError
from core.logger import get_logger

logger = get_logger(__name__)


class FallbackProvider(TextAIProvider):
    """Prueba varios TextAIProvider en orden hasta que uno responda con éxito."""

    def __init__(self, providers: list[TextAIProvider]):
        if not providers:
            raise ValueError("FallbackProvider necesita al menos un proveedor.")
        self._providers = providers

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        last_error: AIProviderError | None = None

        for index, provider in enumerate(self._providers):
            provider_name = type(provider).__name__
            try:
                return provider.generate(prompt, system_instruction=system_instruction)
            except AIProviderError as error:
                last_error = error
                logger.warning(
                    f"{provider_name} falló ({error}). "
                    f"Probando siguiente proveedor..." if index + 1 < len(self._providers)
                    else f"{provider_name} falló ({error}). No quedan más proveedores."
                )

        raise last_error