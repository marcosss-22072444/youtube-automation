"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de
búsqueda web. Cambiar de Tavily a otro buscador en el futuro consiste
en crear una nueva clase que herede de SearchProvider.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RawSearchResult:
    """Un resultado de búsqueda web crudo, antes de clasificar/verificar."""

    url: str
    title: str
    content: str  # extracto o contenido completo de la página


class SearchProvider(ABC):
    """Interfaz abstracta para cualquier proveedor de búsqueda web."""

    @abstractmethod
    def search(self, query: str, max_results: int) -> list[RawSearchResult]:
        """
        Busca en la web y devuelve resultados crudos (sin clasificar).

        Raises:
            SearchProviderError: si el proveedor falla realmente (no
                simplemente "sin resultados", que debe devolver []).
        """
        raise NotImplementedError