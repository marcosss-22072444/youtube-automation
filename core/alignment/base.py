"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de
alineación forzada (audio + texto conocido -> timestamps por palabra).
Distinto de transcripción: el texto ya se conoce, solo se alinea.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class WordTimestamp:
    """Una palabra con su intervalo de tiempo real en el audio."""

    word: str
    start_seconds: float
    end_seconds: float


class ForcedAlignmentProvider(ABC):
    """Interfaz abstracta para cualquier proveedor de alineación forzada."""

    @abstractmethod
    def align(self, audio_path: Path, text: str) -> list[WordTimestamp]:
        """
        Alinea el texto conocido contra el audio y devuelve timestamps
        reales por palabra, en el mismo orden que aparecen en el texto.

        Raises:
            AlignmentError: si falla la alineación.
        """
        raise NotImplementedError