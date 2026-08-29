"""
tavily_provider.py

Implementación concreta de SearchProvider usando la API de Tavily.
"""

from tavily import TavilyClient

from research.search.base import SearchProvider, RawSearchResult
from research.exceptions import SearchProviderError
from core.logger import get_logger

logger = get_logger(__name__)


class TavilySearchProvider(SearchProvider):
    """Proveedor de búsqueda web usando la API de Tavily."""

    def __init__(self, api_key: str):
        self._client = TavilyClient(api_key=api_key)

    def search(self, query: str, max_results: int) -> list[RawSearchResult]:
        try:
            response = self._client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
            )
        except Exception as error:
            logger.warning(f"Tavily: fallo al buscar '{query}': {error}")
            raise SearchProviderError(f"Fallo en TavilySearchProvider: {error}") from error

        results = []
        for item in response.get("results", []):
            results.append(
                RawSearchResult(
                    url=item.get("url", ""),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                )
            )

        return results