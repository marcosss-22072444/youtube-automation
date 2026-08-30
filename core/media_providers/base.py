"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de
clips de vídeo de stock. Cambiar de Pexels/Pixabay a otro proveedor
en el futuro consiste en crear una nueva clase que herede de
StockClipProvider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ClipCandidate:
    """Representa un clip de vídeo candidato, antes de descargarlo."""

    id: str
    download_url: str
    width: int
    height: int
    duration_seconds: float
    source: str  # "pexels" o "pixabay"


class StockClipProvider(ABC):
    """Interfaz abstracta para cualquier proveedor de vídeos de stock."""

    @abstractmethod
    def search(self, query: str, max_results: int, orientation_hint: str | None = None) -> list[ClipCandidate]:
        """Busca clips candidatos para una consulta de texto."""
        raise NotImplementedError

    @abstractmethod
    def download(self, candidate: ClipCandidate, output_path: Path) -> Path:
        """Descarga el clip candidato indicado a output_path."""
        raise NotImplementedError