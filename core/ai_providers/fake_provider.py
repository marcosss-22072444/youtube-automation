"""
fake_provider.py

Proveedor de IA falso, solo para pruebas locales sin depender de una
API real. Simula respuestas en el mismo formato que espera generator.py.
"""

from core.ai_providers.base import TextAIProvider


class FakeProvider(TextAIProvider):
    """Proveedor de prueba: devuelve una idea fija, sin llamar a ninguna IA real."""

    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        return (
            "TITULO: El misterio del Triángulo de las Bermudas\n"
            "RESUMEN: Repaso a las teorías más creíbles sobre las desapariciones en la zona."
        )