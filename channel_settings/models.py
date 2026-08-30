"""models.py — Ajuste clave-valor por canal (JSON serializado)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any

@dataclass
class ChannelSetting:
    channel_id: int
    setting_key: str
    setting_value: Any
    id: Optional[int] = None
    updated_at: Optional[str] = None

    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = datetime.now().isoformat()