"""
fake_provider.py

Proveedor de IA falso, solo para pruebas locales sin depender de una
API real. Por defecto simula una respuesta de Ideas; se le puede pasar
una respuesta fija distinta para probar otros módulos (ej: Scripts).
"""

from core.ai_providers.base import TextAIProvider

_DEFAULT_RESPONSE = (
    "TITULO: El misterio del Triángulo de las Bermudas\n"
    "RESUMEN: Repaso a las teorías más creíbles sobre las desapariciones en la zona."
)


class FakeProvider(TextAIProvider):
    """Proveedor de prueba: devuelve una respuesta fija, sin llamar a ninguna IA real."""

    def __init__(self, fixed_response: str | None = None):
        self._fixed_response = fixed_response or _DEFAULT_RESPONSE

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        return self._fixed_response