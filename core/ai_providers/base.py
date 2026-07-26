"""
base.py

Define el contrato (interfaz) que debe cumplir cualquier proveedor de IA
de texto. Cambiar de Gemini a OpenAI, Claude, DeepSeek, etc. en el futuro
consiste únicamente en crear una nueva clase que herede de TextAIProvider
e implemente generate() — ningún otro módulo del proyecto necesita cambiar.
"""

from abc import ABC, abstractmethod


class TextAIProvider(ABC):
    """
    Interfaz abstracta para cualquier proveedor de IA de generación de texto.
    Todo módulo del proyecto que necesite IA de texto (ideas, guiones,
    metadatos) debe depender de esta interfaz, nunca de una implementación
    concreta como GeminiProvider directamente.
    """

    @abstractmethod
    def generate(self, prompt: str, system_instruction: str | None = None) -> str:
        """
        Genera texto a partir de un prompt.

        Args:
            prompt: el texto de entrada / instrucción principal.
            system_instruction: instrucción de contexto opcional
                (ej: "Eres un guionista experto en documentales").

        Returns:
            El texto generado por el modelo.

        Raises:
            AIProviderError: si el proveedor falla al generar contenido.
        """
        raise NotImplementedError