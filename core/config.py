"""
config.py

Une la configuración de .env (secretos) y config.yaml (configuración
no sensible) en un único objeto Settings, que el resto del proyecto
usará así: from core.config import settings
"""

import os
import yaml
from dotenv import load_dotenv

from core.constants import CONFIG_FILE, DEFAULT_LOG_LEVEL, DEFAULT_AI_PROVIDER
from core.exceptions import ConfigError

# Carga las variables del archivo .env al entorno del proceso
load_dotenv()


class Settings:
    """
    Objeto único de configuración de todo el proyecto.
    Combina variables de entorno (.env) con config.yaml.
    """

    def __init__(self):
        # --- Secretos desde .env ---
        self.gemini_api_key: str = self._get_required_env("GEMINI_API_KEY")
        self.groq_api_key: str = self._get_required_env("GROQ_API_KEY")
        self.hf_api_token: str = self._get_required_env("HF_API_TOKEN")
        self.pexels_api_key: str = self._get_required_env("PEXELS_API_KEY")
        self.pixabay_api_key: str = self._get_required_env("PIXABAY_API_KEY")

        # --- Configuración no sensible desde config.yaml ---
        yaml_config = self._load_yaml_config()

        self.log_level: str = yaml_config.get("log_level", DEFAULT_LOG_LEVEL)
        self.ai_provider: str = yaml_config.get("ai_provider", DEFAULT_AI_PROVIDER)
        self.gemini_model: str = yaml_config.get("gemini_model", "gemini-3.6-flash")
        self.groq_model: str = yaml_config.get("groq_model", "openai/gpt-oss-120b")
        self.ideas_context_limit: int = yaml_config.get("ideas_context_limit", 50)
        self.narration_wpm: int = yaml_config.get("narration_wpm", 150)
        self.script_duration_seconds: dict = yaml_config.get(
            "script_duration_seconds", {"short": 45, "long": 480}
        )
        self.image_generation: dict = yaml_config.get(
            "image_generation",
            {"width": 768, "height": 768, "num_inference_steps": 20, "guidance_scale": 7.0},
        )
        self.voice_naturalness: dict = yaml_config.get(
            "voice_naturalness", {"speed": 0.95, "pause_between_segments_ms": 200}
        )
        self.text_normalization: dict = yaml_config.get(
            "text_normalization",
            {
            "use_ai_pass": True,
            "unit_expansions": {
                "km/h": "kilómetros por hora",
                "km": "kilómetros",
                "kg": "kilogramos",
                "cm": "centímetros",
                "mm": "milímetros",
                "hp": "caballos de fuerza",
                "mph": "millas por hora",
                "kmh": "kilómetros por hora",
                }
            },
        )
        self.scheduler: dict = yaml_config.get(
            "scheduler",
            {
                "timezone": "Europe/Madrid",
                "check_interval_seconds": 60,
                "default_privacy_status": "private",
                "worker_count": 1,
            },
        )
        self.error_handler: dict = yaml_config.get(
            "error_handler",
            {"max_retries": 3, "base_retry_delay_seconds": 60, "max_retry_delay_seconds": 900},
        )
        self.credentials: dict = yaml_config.get(
            "credentials", {"allow_global_fallback": True}
        )
        self.thumbnails: dict = yaml_config.get(
            "thumbnails",
            {
                "dimensions": {
                    "short": {"width": 1080, "height": 1920},
                    "long": {"width": 1280, "height": 720},
                },
                "font_path": "assets/fonts/Anton-Regular.ttf",
                "font_size": "auto", "max_font_size": 140, "min_font_size": 60,
                "font_color": "auto", "outline_width": 8, "max_lines": 3,
            },
        )
        self.media_sources: dict = yaml_config.get(
            "media_sources",
            {
                "order": ["pexels", "pixabay", "sdxl"],
                "avoid_repetition": True,
                "candidates_per_search": 5,
                "request_delay_seconds": {"min": 2.0, "max": 3.0},
                "pause_every_n_scenes": 30,
                "pause_seconds": {"min": 15.0, "max": 30.0},
            },
        )
        self.video: dict = yaml_config.get(
            "video",
            {
                "scene_duration": {
                    "short": {"min_seconds": 1.5, "max_seconds": 2.0},
                    "long": {"min_seconds": 4.0, "max_seconds": 6.0},
                },
                "ken_burns": {"enabled": True, "zoom_start": 1.0, "zoom_end": 1.15, "pan_enabled": True},
                "subtitles": {
                    "enabled": True,
                    "export_srt": True,
                    "burn_in": True,
                    "font_size": 48,
                    "font_color": "white",
                    "outline_color": "black",
                    "outline_width": 2,
                    "position": "bottom",
                    "max_lines": 2,
                    "animation": "none",
                },
            },
        )
        

    @staticmethod
    def _get_required_env(var_name: str) -> str:
        """Lee una variable de entorno obligatoria; lanza ConfigError si falta."""
        value = os.getenv(var_name)
        if not value or value == "tu_clave_aqui":
            raise ConfigError(
                f"Falta la variable de entorno '{var_name}'. "
                f"Revisa tu archivo .env"
            )
        return value

    @staticmethod
    def _load_yaml_config() -> dict:
        """Lee y parsea config.yaml. Si no existe, devuelve un diccionario vacío."""
        if not CONFIG_FILE.exists():
            return {}
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return yaml.safe_load(file) or {}


# Instancia única (singleton) que todo el proyecto importará directamente
settings = Settings()