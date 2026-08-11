"""
text_normalizer.py

Normaliza el texto antes de pasarlo a un motor TTS: expande
abreviaturas de unidades (configurables en config.yaml) y convierte
números en dígitos a su forma escrita en español, para que la
narración suene natural ("1200" -> "mil doscientos") en vez de
deletrear dígito a dígito.
"""

import re

from num2words import num2words

from core.config import settings


def _expand_units(text: str) -> str:
    """Sustituye abreviaturas de unidades por su forma completa,
    usando el diccionario configurado en config.yaml."""
    expansions = settings.text_normalization.get("unit_expansions", {})

    # Ordenamos por longitud descendente para que "km/h" se sustituya
    # antes que "km" y no queden restos ("kilómetros/h").
    for abbreviation in sorted(expansions, key=len, reverse=True):
        pattern = r"\b" + re.escape(abbreviation) + r"\b"
        text = re.sub(pattern, expansions[abbreviation], text, flags=re.IGNORECASE)

    return text


def _numbers_to_words(text: str) -> str:
    """Convierte números en dígitos a su forma escrita en español."""

    def _replace(match: re.Match) -> str:
        number_str = match.group(0).replace(".", "").replace(",", ".")
        try:
            if "." in number_str:
                return num2words(float(number_str), lang="es")
            return num2words(int(number_str), lang="es")
        except ValueError:
            return match.group(0)

    return re.sub(r"\b\d[\d.,]*\b", _replace, text)


_AI_SYSTEM_INSTRUCTION = (
    "Eres un normalizador de texto para locución (text-to-speech). Recibes "
    "un texto en español y debes reescribirlo EXACTAMENTE igual, palabra "
    "por palabra, con una única diferencia: expande cualquier abreviatura, "
    "sigla, símbolo o unidad a su forma completa hablada en español "
    "(ej: 'Dr.' -> 'doctor', 'EE.UU.' -> 'Estados Unidos', '%' -> 'por ciento', "
    "'€' -> 'euros', '2ª' -> 'segunda'). "
    "NO resumas, NO cambies el significado, NO añadas ni quites frases, "
    "NO cambies el estilo. Responde ÚNICAMENTE con el texto reescrito, "
    "sin ninguna explicación ni comentario adicional."
)


def normalize_text_for_tts(text: str) -> str:
    """Aplica las normalizaciones deterministas (config.yaml) antes de
    enviar el texto a un TTS."""
    text = _expand_units(text)
    text = _numbers_to_words(text)
    return text


def normalize_text_for_tts_with_ai(text: str, provider=None) -> str:
    """
    Pasada adicional con IA de texto: expande CUALQUIER abreviatura,
    sigla o símbolo que la lista manual de config.yaml no cubra. Usa el
    proveedor de IA por defecto (con fallback Gemini->Groq). Si la IA
    falla, devuelve el texto tal cual (ya con las normalizaciones
    manuales aplicadas), para no bloquear la generación de voz.
    """
    if not settings.text_normalization.get("use_ai_pass", True):
        return text

    if provider is None:
        from core.ai_providers.factory import get_default_text_provider
        provider = get_default_text_provider()

    try:
        return provider.generate(text, system_instruction=_AI_SYSTEM_INSTRUCTION).strip()
    except Exception as error:
        from core.logger import get_logger
        get_logger(__name__).warning(f"Fallo en normalización con IA, se usa el texto sin expandir del todo: {error}")
        return text