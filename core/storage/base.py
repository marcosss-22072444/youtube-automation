"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier backend de
almacenamiento. Todo el proyecto guarda y lee archivos a través de
esta interfaz usando "claves" lógicas (ej: "voice/script_9.wav"),
nunca rutas absolutas directamente. Cambiar de almacenamiento local a
uno en la nube (S3, etc.) en el futuro consiste en crear una nueva
clase que herede de StorageBackend — ningún otro módulo cambia.
"""

from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Interfaz abstracta para cualquier backend de almacenamiento de archivos."""

    @abstractmethod
    def save(self, local_source_path: Path, key: str) -> str:
        """
        Publica un archivo que ya existe en local bajo la clave indicada.

        Args:
            local_source_path: ruta local del archivo ya generado.
            key: clave lógica bajo la que se guardará (ej: "voice/script_9.wav").

        Returns:
            La clave (str) bajo la que quedó guardado.
        """
        raise NotImplementedError

    @abstractmethod
    def resolve_path(self, key: str) -> Path:
        """
        Devuelve una ruta local real y utilizable para la clave dada,
        descargando el archivo primero si el backend no fuera local.
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Indica si existe algo guardado bajo esa clave."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        """Elimina lo guardado bajo esa clave."""
        raise NotImplementedError