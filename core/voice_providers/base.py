"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de
voz IA. Cambiar de Kokoro a otro motor en el futuro consiste en crear
una nueva clase que herede de VoiceProvider — ningún otro módulo del
proyecto necesita cambiar.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class VoiceProvider(ABC):
    """Interfaz abstracta para cualquier proveedor de voz IA (texto -> audio)."""

    @abstractmethod
    def generate(
        self, text: str, voice_name: str, output_path: Path,
        speed: float | None = None, pause_ms: int | None = None,
    ) -> Path:
        """
        Genera audio narrado a partir de un texto, usando la voz indicada,
        y lo guarda en output_path.

        Args:
            text: el guion completo a narrar.
            voice_name: identificador de la voz a usar (depende del proveedor).
            output_path: ruta donde guardar el archivo de audio generado.

        Returns:
            La ruta (Path) del archivo de audio generado.

        Raises:
            VoiceProviderError: si el proveedor falla al generar el audio.
        """
        raise NotImplementedError