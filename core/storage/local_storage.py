"""
local_storage.py

Implementación de StorageBackend que guarda los archivos en el disco
local, dentro de la carpeta output/. Las claves lógicas (ej:
"voice/script_9.wav") se traducen directamente a rutas relativas
dentro de esa carpeta.
"""

import shutil
from pathlib import Path

from core.storage.base import StorageBackend
from core.constants import OUTPUT_DIR
from core.exceptions import BaseAppError


class StorageKeyNotFoundError(BaseAppError):
    """Se lanza cuando se pide una clave que no existe en el almacenamiento."""
    pass


class LocalStorage(StorageBackend):
    """Backend de almacenamiento local, dentro de output/."""

    def __init__(self, base_dir: Path | None = None):
        self._base_dir = base_dir or OUTPUT_DIR

    def _key_to_path(self, key: str) -> Path:
        return self._base_dir / key

    def save(self, local_source_path: Path, key: str) -> str:
        destination = self._key_to_path(key)
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Si el archivo ya está en su destino final (caso habitual: los
        # generadores ya escriben directamente ahí), no hace falta copiar.
        if local_source_path.resolve() != destination.resolve():
            shutil.copyfile(local_source_path, destination)

        return key

    def resolve_path(self, key: str) -> Path:
        path = self._key_to_path(key)
        if not path.exists():
            raise StorageKeyNotFoundError(f"No existe ningún archivo bajo la clave '{key}'.")
        return path

    def exists(self, key: str) -> bool:
        return self._key_to_path(key).exists()

    def delete(self, key: str) -> None:
        path = self._key_to_path(key)
        if path.exists():
            path.unlink()