"""
huggingface_flux_provider.py

Implementación concreta de ImageProvider usando FLUX Schnell a través
de la Inference API de Hugging Face.
"""

from pathlib import Path

from huggingface_hub import InferenceClient

from core.image_providers.base import ImageProvider
from core.config import settings
from core.exceptions import ImageProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_MODEL = "black-forest-labs/FLUX.1-schnell"


class HuggingFaceFluxProvider(ImageProvider):
    """Proveedor de imágenes usando FLUX Schnell vía Hugging Face Inference API."""

    def __init__(self):
        self._client = InferenceClient(token=settings.hf_api_token)

    def generate(self, prompt: str, output_path: Path) -> Path:
        try:
            image = self._client.text_to_image(prompt, model=_MODEL)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path)

            return output_path

        except Exception as error:
            logger.error(f"Error al generar imagen con FLUX: {error}")
            raise ImageProviderError(f"Fallo en HuggingFaceFluxProvider: {error}") from error