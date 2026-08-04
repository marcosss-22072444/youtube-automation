"""
sdxl_local_provider.py

Implementación concreta de ImageProvider usando SDXL Base, ejecutado
localmente con la GPU (CUDA) a través de la librería diffusers.
Optimizado para GPUs con VRAM limitada (ej: 8GB): resolución, pasos
y demás parámetros son configurables desde config.yaml, para poder
subir la calidad fácilmente al usar una GPU más potente en el futuro.
"""

from pathlib import Path

import torch
from diffusers import StableDiffusionXLPipeline

from core.image_providers.base import ImageProvider
from core.config import settings
from core.exceptions import ImageProviderError
from core.logger import get_logger

logger = get_logger(__name__)

_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"


class SDXLLocalProvider(ImageProvider):
    """Proveedor de imágenes usando SDXL Base, ejecutado localmente en GPU."""

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        logger.info(f"Cargando SDXL Base en '{device}' (esto puede tardar la primera vez)...")

        self._pipeline = StableDiffusionXLPipeline.from_pretrained(
            _MODEL_ID,
            torch_dtype=dtype,
            use_safetensors=True,
        )
        self._pipeline.to(device)

        # Optimizaciones de memoria, importantes en GPUs de VRAM limitada
        # (ej: 8GB). Si en el futuro usas una GPU con más VRAM, puedes
        # quitar estas líneas para ganar algo de velocidad extra.
        self._pipeline.enable_attention_slicing()
        self._pipeline.enable_vae_slicing()
        self._pipeline.enable_vae_tiling()

    def generate(self, prompt: str, output_path: Path) -> Path:
        config = settings.image_generation

        try:
            result = self._pipeline(
                prompt=prompt,
                width=config["width"],
                height=config["height"],
                num_inference_steps=config["num_inference_steps"],
                guidance_scale=config["guidance_scale"],
            )
            image = result.images[0]

            output_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(output_path)

            return output_path

        except Exception as error:
            logger.error(f"Error al generar imagen con SDXL local: {error}")
            raise ImageProviderError(f"Fallo en SDXLLocalProvider: {error}") from error