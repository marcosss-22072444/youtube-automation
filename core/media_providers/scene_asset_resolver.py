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
from core.credentials.base import resolve_credential
from core.credentials.factory import get_default_credentials_store
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

    def __init__(self, channel_id: int, image_provider: ImageProvider | None = None):
        self._image_provider = image_provider or get_default_image_provider()
        self._used_clip_ids: set[str] = set()

        store = get_default_credentials_store()
        order = settings.media_sources["order"]

        self._clip_providers: list[StockClipProvider] = []
        for name in order:
            if name not in _PROVIDER_REGISTRY:
                continue
            if name == "pexels":
                api_key = resolve_credential(channel_id, "pexels", settings.pexels_api_key, store)
                self._clip_providers.append(PexelsProvider(api_key=api_key))
            elif name == "pixabay":
                api_key = resolve_credential(channel_id, "pixabay", settings.pixabay_api_key, store)
                self._clip_providers.append(PixabayProvider(api_key=api_key))

        # Proveedores marcados como no disponibles durante este vídeo
        # (ej: bloqueados por rate limit) — no se vuelven a intentar.
        self._unavailable_providers: set[int] = set()

    def resolve(self, queries: list[str], content_type: str, output_path: Path) -> tuple[str, str]:
        """
        queries: lista ordenada de mas especifica a mas generica (nivel 1..N).
        Prioridad: nivel de especificidad > orientacion > proveedor.
        Nunca baja de nivel si el nivel actual tuvo resultados (en cualquier orientacion).
        """
        candidates_per_search = settings.media_sources["candidates_per_search"]
        avoid_repetition = settings.media_sources["avoid_repetition"]
        preferred_orientation = settings.visuals_matching["orientation_priority"].get(content_type, "vertical")
        other_orientation = "horizontal" if preferred_orientation == "vertical" else "vertical"

        for query in queries:
            for orientation in (preferred_orientation, other_orientation):
                for provider in self._clip_providers:
                    if id(provider) in self._unavailable_providers:
                        continue

                    try:
                        candidates = provider.search(query, candidates_per_search, orientation_hint=orientation)
                    except ProviderUnavailableError as error:
                        logger.warning(f"{type(provider).__name__} no disponible: {error}")
                        self._unavailable_providers.add(id(provider))
                        continue

                    candidates = self._rank_by_orientation(candidates, orientation)

                    if avoid_repetition:
                        fresh = [c for c in candidates if c.id not in self._used_clip_ids]
                        chosen_pool = fresh or candidates
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
                    logger.info(f"Escena resuelta: '{query}' ({orientation}) -> {candidate.source}")
                    return "video", candidate.source

        logger.info(f"Sin clips de stock para ninguna consulta, generando imagen con SDXL: '{queries[-1]}'")
        self._image_provider.generate(queries[-1], output_path)
        return "image", "sdxl"

    @staticmethod
    def _rank_by_orientation(candidates: list, preferred: str) -> list:
        def matches(c):
            is_vertical = c.height > c.width
            return (preferred == "vertical") == is_vertical
        return sorted(candidates, key=lambda c: not matches(c))