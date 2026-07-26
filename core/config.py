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

        # --- Configuración no sensible desde config.yaml ---
        yaml_config = self._load_yaml_config()

        self.log_level: str = yaml_config.get("log_level", DEFAULT_LOG_LEVEL)
        self.ai_provider: str = yaml_config.get("ai_provider", DEFAULT_AI_PROVIDER)
        self.gemini_model: str = yaml_config.get("gemini_model", "gemini-3.6-flash")
        self.ideas_context_limit: int = yaml_config.get("ideas_context_limit", 50)

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