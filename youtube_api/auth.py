"""
auth.py

Gestiona la autenticación OAuth de YouTube, de forma independiente
por canal. Cada canal guarda su propio token en
data/youtube_tokens/{channel_id}.json, y lo reutiliza/refresca
automáticamente en subidas futuras sin pedir login de nuevo.
"""

import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from core.constants import YOUTUBE_TOKENS_DIR, CLIENT_SECRET_FILE
from youtube_api.exceptions import YouTubeAuthError
from core.logger import get_logger

logger = get_logger(__name__)

_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _token_path(channel_id: int):
    return YOUTUBE_TOKENS_DIR / f"{channel_id}.json"


def get_credentials(channel_id: int) -> Credentials:
    """
    Devuelve credenciales válidas para el canal indicado, reutilizando
    o refrescando el token guardado si existe, o iniciando el flujo de
    autorización en el navegador si es la primera vez.
    """
    if not CLIENT_SECRET_FILE.exists():
        raise YouTubeAuthError(
            f"No se encontró {CLIENT_SECRET_FILE.name}. Descárgalo desde "
            f"Google Cloud Console y colócalo en la raíz del proyecto."
        )

    token_path = _token_path(channel_id)
    credentials = None

    if token_path.exists():
        credentials = Credentials.from_authorized_user_file(str(token_path), _SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        logger.info(f"Canal {channel_id}: iniciando autorización OAuth en el navegador...")
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET_FILE), _SCOPES)
        credentials = flow.run_local_server(port=0)

    token_path.write_text(credentials.to_json(), encoding="utf-8")
    return credentials


def get_youtube_client(channel_id: int):
    """Devuelve un cliente autenticado de la API de YouTube para el canal indicado."""
    credentials = get_credentials(channel_id)
    return build("youtube", "v3", credentials=credentials)