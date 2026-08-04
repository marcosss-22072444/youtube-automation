"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de
generación de imágenes. Cambiar de FLUX a otro modelo en el futuro
consiste en crear una nueva clase que herede de ImageProvider.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class ImageProvider(ABC):
    """Interfaz abstracta para cualquier proveedor de generación de imágenes."""

    @abstractmethod
    def generate(self, prompt: str, output_path: Path) -> Path:
        """
        Genera una imagen a partir de un prompt de texto y la guarda
        en output_path.

        Args:
            prompt: descripción visual de la imagen a generar.
            output_path: ruta donde guardar la imagen generada.

        Returns:
            La ruta (Path) de la imagen generada.

        Raises:
            ImageProviderError: si el proveedor falla al generar la imagen.
        """
        raise NotImplementedError