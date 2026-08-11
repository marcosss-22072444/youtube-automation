"""
pixabay_provider.py

Implementación concreta de StockClipProvider usando la API de vídeos
de Pixabay.
"""

from pathlib import Path

import requests

from core.media_providers.base import StockClipProvider, ClipCandidate
from core.config import settings
from core.exceptions import BaseAppError
from core.logger import get_logger

logger = get_logger(__name__)

_SEARCH_URL = "https://pixabay.com/api/videos/"


class PixabayProviderError(BaseAppError):
    """Se lanza cuando falla la búsqueda o descarga de un clip de Pixabay."""
    pass


class PixabayProvider(StockClipProvider):
    """Proveedor de vídeos de stock usando la API de Pixabay."""

    def search(self, query: str, max_results: int) -> list[ClipCandidate]:
        try:
            response = requests.get(
                _SEARCH_URL,
                params={
                    "key": settings.pixabay_api_key,
                    "q": query,
                    "per_page": max_results,
                    "video_type": "film",
                },
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            logger.warning(f"Pixabay: fallo al buscar '{query}': {error}")
            return []

        candidates = []
        for video in data.get("hits", []):
            best_file = self._pick_best_file(video.get("videos", {}))
            if best_file is None:
                continue

            candidates.append(
                ClipCandidate(
                    id=f"pixabay_{video['id']}",
                    download_url=best_file["url"],
                    width=best_file.get("width", 0),
                    height=best_file.get("height", 0),
                    duration_seconds=video.get("duration", 0),
                    source="pixabay",
                )
            )

        return candidates

    def _pick_best_file(self, videos: dict) -> dict | None:
        """Pixabay no ofrece vídeos verticales nativos: elige la mejor
        calidad disponible (large > medium > small > tiny). El recorte
        a formato vertical se hace después en el montaje (scale+crop)."""
        for quality in ("large", "medium", "small", "tiny"):
            if quality in videos and videos[quality].get("url"):
                return videos[quality]
        return None

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
            raise PixabayProviderError(f"Fallo al descargar clip de Pixabay: {error}") from error