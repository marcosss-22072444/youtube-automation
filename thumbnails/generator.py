"""
generator.py

Genera la miniatura de un vídeo: una imagen de fondo (usando el
ImageProvider configurado, SDXL local por defecto) con el título
superpuesto, ajustando automáticamente el color del texto (por
contraste) y el tamaño de fuente (para que el título quepa).
"""

import tempfile
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from thumbnails import repository as thumbnail_repository
from thumbnails.models import Thumbnail
from thumbnails.exceptions import ThumbnailGenerationError
from core.image_providers.base import ImageProvider
from core.image_providers.factory import get_default_image_provider
from core.storage.base import StorageBackend
from core.storage.factory import get_default_storage
from core.constants import BASE_DIR
from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


def _detect_text_color(image: Image.Image) -> tuple[str, str]:
    """
    Analiza el brillo medio de la zona central de la imagen y decide
    color de texto/borde con buen contraste.

    Returns:
        (color_texto, color_borde) en formato aceptado por Pillow.
    """
    width, height = image.size
    region = image.crop((0, height // 4, width, height * 3 // 4)).convert("L")
    average_brightness = sum(region.getdata()) / (region.width * region.height)

    if average_brightness < 128:
        return "white", "black"
    return "black", "white"


def _fit_text(
    draw: ImageDraw.ImageDraw, text: str, font_path: str,
    max_width: int, max_lines: int, max_size: int, min_size: int,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    """
    Prueba tamaños de fuente de mayor a menor hasta encontrar uno cuyo
    título, envuelto en máximo max_lines líneas, quepa en max_width.
    """
    for font_size in range(max_size, min_size - 1, -5):
        font = ImageFont.truetype(font_path, font_size)

        # Estimamos cuántos caracteres caben por línea a este tamaño,
        # probando anchos de wrap crecientes hasta encajar en max_lines.
        for chars_per_line in range(10, 60):
            lines = textwrap.wrap(text, width=chars_per_line)
            if len(lines) > max_lines:
                continue

            widths = [draw.textlength(line, font=font) for line in lines]
            if max(widths, default=0) <= max_width:
                return font, lines

    # Si nada encajó, devolvemos el tamaño mínimo con el wrap más agresivo posible.
    font = ImageFont.truetype(font_path, min_size)
    lines = textwrap.wrap(text, width=15)[:max_lines]
    return font, lines


def generate_thumbnail_for_script(
    script_id: int,
    title: str,
    background_prompt: str,
    image_provider: ImageProvider | None = None,
    storage: StorageBackend | None = None,
) -> Thumbnail:
    """
    Genera la miniatura para un vídeo: fondo generado con IA + título
    superpuesto con color y tamaño de fuente automáticos.
    """
    if image_provider is None:
        image_provider = get_default_image_provider()
    if storage is None:
        storage = get_default_storage()

    config = settings.thumbnails
    font_path = str(BASE_DIR / config["font_path"])

    with tempfile.TemporaryDirectory() as tmp:
        temp_dir = Path(tmp)
        background_path = temp_dir / "background.png"

        try:
            image_provider.generate(background_prompt, background_path)
            image = Image.open(background_path).convert("RGB")
            image = image.resize((config["width"], config["height"]))
        except Exception as error:
            raise ThumbnailGenerationError(f"Fallo al generar el fondo de la miniatura: {error}") from error

        draw = ImageDraw.Draw(image)

        if config["font_color"] == "auto":
            text_color, outline_color = _detect_text_color(image)
        else:
            text_color = config["font_color"]
            outline_color = config.get("outline_color", "black")

        max_width = int(config["width"] * 0.9)
        font, lines = _fit_text(
            draw, title, font_path, max_width,
            config["max_lines"], config["max_font_size"], config["min_font_size"],
        )

        line_height = font.getbbox("Ay")[3] + 10
        total_text_height = line_height * len(lines)
        y = (config["height"] - total_text_height) // 2

        for line in lines:
            line_width = draw.textlength(line, font=font)
            x = (config["width"] - line_width) // 2
            draw.text(
                (x, y), line, font=font, fill=text_color,
                stroke_width=config["outline_width"], stroke_fill=outline_color,
            )
            y += line_height

        final_path = temp_dir / f"script_{script_id}.png"
        image.save(final_path)

        key = f"thumbnails/script_{script_id}.png"
        storage.save(final_path, key)

    thumbnail = Thumbnail(script_id=script_id, file_path=key, title_text=title)
    saved_thumbnail = thumbnail_repository.create(thumbnail)
    logger.info(f"Miniatura generada para guion {script_id}: {key}")
    return saved_thumbnail