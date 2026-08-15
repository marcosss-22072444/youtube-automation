"""
pexels_provider.py

Implementación concreta de StockClipProvider usando la API de vídeos
de Pexels.
"""

import requests
from pathlib import Path
from core.media_providers.base import StockClipProvider, ClipCandidate
from core.media_providers.exceptions import ProviderUnavailableError
from core.config import settings
from core.exceptions import BaseAppError
from core.logger import get_logger

logger = get_logger(__name__)

_SEARCH_URL = "https://api.pexels.com/videos/search"
_TARGET_WIDTH = 1080
_TARGET_HEIGHT = 1920


class PexelsProviderError(BaseAppError):
    """Se lanza cuando falla la búsqueda o descarga de un clip de Pexels."""
    pass


class PexelsProvider(StockClipProvider):
    """Proveedor de vídeos de stock usando la API de Pexels."""

    def __init__(self):
        self._headers = {"Authorization": settings.pexels_api_key}

    def search(self, query: str, max_results: int) -> list[ClipCandidate]:
        try:
            response = requests.get(
                _SEARCH_URL,
                headers=self._headers,
                params={"query": query, "per_page": max_results, "orientation": "portrait"},
                timeout=15,
            )
        except requests.RequestException as error:
            logger.warning(f"Pexels: error de red, se marca como no disponible: {error}")
            raise ProviderUnavailableError(f"Pexels no disponible (red): {error}") from error

        if response.status_code == 429:
            logger.warning("Pexels: límite de peticiones alcanzado (429), se marca como no disponible.")
            raise ProviderUnavailableError("Pexels devolvió 429 (rate limit).")

        if response.status_code >= 500:
            logger.warning(f"Pexels: error del servidor ({response.status_code}), se marca como no disponible.")
            raise ProviderUnavailableError(f"Pexels devolvió {response.status_code}.")

        try:
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning(f"Pexels: fallo al buscar '{query}': {error}")
            return []

        candidates = []
        for video in data.get("videos", []):
            best_file = self._pick_best_file(video.get("video_files", []))
            if best_file is None:
                continue

            candidates.append(
                ClipCandidate(
                    id=f"pexels_{video['id']}",
                    download_url=best_file["link"],
                    width=best_file.get("width", 0),
                    height=best_file.get("height", 0),
                    duration_seconds=video.get("duration", 0),
                    source="pexels",
                )
            )

        return candidates

    def _pick_best_file(self, video_files: list[dict]) -> dict | None:
        """Elige el archivo mp4 vertical más cercano a la resolución objetivo,
        sin pasarse (para no descargar más peso del necesario)."""
        mp4_files = [f for f in video_files if f.get("file_type") == "video/mp4"]
        vertical_files = [f for f in mp4_files if f.get("height", 0) > f.get("width", 0)]

        candidates = vertical_files or mp4_files
        if not candidates:
            return None

        return min(
            candidates,
            key=lambda f: abs(f.get("height", 0) - _TARGET_HEIGHT),
        )

    def download(self, candidate: ClipCandidate, output_path: Path) -> Path:
        try:
            response = requests.get(candidate.download_url, timeout=30, stream=True)
            response.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            return output_path

        except Exception as error:
            raise PexelsProviderError(f"Fallo al descargar clip de Pexels: {error}") from error