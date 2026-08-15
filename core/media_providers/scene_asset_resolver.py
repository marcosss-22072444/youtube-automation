"""
scene_asset_resolver.py

Resuelve el asset visual de una escena: prueba proveedores de vídeo de
stock en el orden configurado (Pexels -> Pixabay), evitando repetir
clips ya usados en el mismo vídeo salvo que sea imprescindible. Si
ningún proveedor encuentra un clip válido, recurre a generar una
imagen con SDXL local como último recurso.
"""

from pathlib import Path

from core.media_providers.base import StockClipProvider
from core.media_providers.exceptions import ProviderUnavailableError
from core.media_providers.pexels_provider import PexelsProvider
from core.media_providers.pixabay_provider import PixabayProvider
from core.image_providers.base import ImageProvider
from core.image_providers.factory import get_default_image_provider
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)

_PROVIDER_REGISTRY: dict[str, type[StockClipProvider]] = {
    "pexels": PexelsProvider,
    "pixabay": PixabayProvider,
}


class SceneAssetResolver:
    """
    Orquesta la búsqueda de un asset visual por escena: vídeo de stock
    primero (en el orden configurado), imagen local (SDXL) como último
    recurso.
    """

    def __init__(self, image_provider: ImageProvider | None = None):
        self._image_provider = image_provider or get_default_image_provider()
        self._used_clip_ids: set[str] = set()

        order = settings.media_sources["order"]
        self._clip_providers: list[StockClipProvider] = [
            _PROVIDER_REGISTRY[name]() for name in order if name in _PROVIDER_REGISTRY
        ]
        # Proveedores marcados como no disponibles durante este vídeo
        # (ej: bloqueados por rate limit) — no se vuelven a intentar.
        self._unavailable_providers: set[int] = set()

    def resolve(self, query: str, output_path: Path) -> tuple[str, str]:
        """
        Resuelve el asset de una escena y lo guarda en output_path.
        Si un proveedor de stock falla de forma que indica que está
        bloqueado (ProviderUnavailableError), se marca como no
        disponible para el resto de este vídeo y se pasa directamente
        al siguiente proveedor, sin volver a intentarlo.

        Returns:
            (asset_type, source): ("video", "pexels"/"pixabay") o ("image", "sdxl").
        """
        candidates_per_search = settings.media_sources["candidates_per_search"]
        avoid_repetition = settings.media_sources["avoid_repetition"]

        for provider in self._clip_providers:
            if id(provider) in self._unavailable_providers:
                continue

            try:
                candidates = provider.search(query, candidates_per_search)
            except ProviderUnavailableError as error:
                logger.warning(
                    f"{type(provider).__name__} no disponible, se omite el resto "
                    f"del vídeo para este proveedor: {error}"
                )
                self._unavailable_providers.add(id(provider))
                continue

            if avoid_repetition:
                fresh = [c for c in candidates if c.id not in self._used_clip_ids]
                chosen_pool = fresh or candidates  # si se agotan, se permite repetir
            else:
                chosen_pool = candidates

            if not chosen_pool:
                continue

            candidate = chosen_pool[0]
            try:
                provider.download(candidate, output_path)
            except Exception as error:
                logger.warning(f"Fallo al descargar candidato de {candidate.source}: {error}")
                continue

            self._used_clip_ids.add(candidate.id)
            logger.info(f"Escena resuelta con clip de {candidate.source} ('{query}').")
            return "video", candidate.source

        logger.info(f"Ningún clip de stock encontrado para '{query}', generando imagen con SDXL.")
        self._image_provider.generate(query, output_path)
        return "image", "sdxl"