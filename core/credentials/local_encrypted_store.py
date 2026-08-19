"""
local_encrypted_store.py

Implementación de CredentialsStore que guarda las credenciales de
cada canal en un archivo cifrado independiente
(data/channel_credentials/{channel_id}.enc), usando una clave maestra
autogenerada en data/.credentials_key (nunca se sube a git).
"""

import json

from cryptography.fernet import Fernet, InvalidToken

from core.credentials.base import CredentialsStore
from core.constants import CHANNEL_CREDENTIALS_DIR, CREDENTIALS_KEY_FILE
from core.exceptions import BaseAppError
from core.logger import get_logger

logger = get_logger(__name__)


class CredentialsDecryptionError(BaseAppError):
    """Se lanza cuando falla el descifrado de las credenciales de un canal."""
    pass


def _get_or_create_master_key() -> bytes:
    """Devuelve la clave maestra, generándola la primera vez si no existe."""
    if CREDENTIALS_KEY_FILE.exists():
        return CREDENTIALS_KEY_FILE.read_bytes()

    key = Fernet.generate_key()
    CREDENTIALS_KEY_FILE.write_bytes(key)
    logger.info(
        "Generada nueva clave maestra de credenciales en "
        f"{CREDENTIALS_KEY_FILE.name} (no se sube a git; consérvala si "
        "quieres conservar las credenciales guardadas)."
    )
    return key


class LocalEncryptedCredentialsStore(CredentialsStore):
    """Almacén de credenciales cifrado localmente, un archivo por canal."""

    def __init__(self):
        self._fernet = Fernet(_get_or_create_master_key())

    def _file_path(self, channel_id: int):
        return CHANNEL_CREDENTIALS_DIR / f"{channel_id}.enc"

    def _read_all(self, channel_id: int) -> dict:
        """Descifra y devuelve todas las credenciales de un canal, o {} si no hay ninguna."""
        path = self._file_path(channel_id)
        if not path.exists():
            return {}

        try:
            decrypted = self._fernet.decrypt(path.read_bytes())
            return json.loads(decrypted.decode("utf-8"))
        except InvalidToken as error:
            raise CredentialsDecryptionError(
                f"No se pudo descifrar el archivo de credenciales del canal {channel_id}. "
                f"¿Cambió la clave maestra?"
            ) from error

    def _write_all(self, channel_id: int, data: dict) -> None:
        """Cifra y guarda el diccionario completo de credenciales de un canal."""
        encrypted = self._fernet.encrypt(json.dumps(data).encode("utf-8"))
        self._file_path(channel_id).write_bytes(encrypted)

    def get(self, channel_id: int, provider_name: str) -> str | None:
        return self._read_all(channel_id).get(provider_name)

    def set(self, channel_id: int, provider_name: str, value: str) -> None:
        data = self._read_all(channel_id)
        data[provider_name] = value
        self._write_all(channel_id, data)
        logger.info(f"Canal {channel_id}: credencial de '{provider_name}' guardada (valor no registrado en log).")

    def delete(self, channel_id: int, provider_name: str) -> None:
        data = self._read_all(channel_id)
        if provider_name in data:
            del data[provider_name]
            self._write_all(channel_id, data)
            logger.info(f"Canal {channel_id}: credencial de '{provider_name}' eliminada.")

    def list_configured_providers(self, channel_id: int) -> list[str]:
        return list(self._read_all(channel_id).keys())