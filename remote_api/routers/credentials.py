"""credentials.py — Endpoints REST de credenciales por canal. NUNCA expone valores."""
from fastapi import APIRouter
from pydantic import BaseModel

from core.credentials.factory import get_default_credentials_store

router = APIRouter(prefix="/credentials", tags=["credentials"])
_ALLOWED_PROVIDERS = ("gemini", "groq", "pexels", "pixabay", "tavily")


class CredentialSet(BaseModel):
    provider_name: str
    value: str


@router.get("/{channel_id}")
def list_configured(channel_id: int):
    """Devuelve solo QUE proveedores tienen credencial propia, nunca el valor."""
    store = get_default_credentials_store()
    configured = store.list_configured_providers(channel_id)
    return {"configured_providers": configured}


@router.post("/{channel_id}")
def set_credential(channel_id: int, data: CredentialSet):
    if data.provider_name not in _ALLOWED_PROVIDERS:
        return {"error": f"provider_name debe ser uno de: {_ALLOWED_PROVIDERS}"}
    store = get_default_credentials_store()
    store.set(channel_id, data.provider_name, data.value)
    return {"channel_id": channel_id, "provider_name": data.provider_name, "status": "guardado"}


@router.delete("/{channel_id}/{provider_name}")
def delete_credential(channel_id: int, provider_name: str):
    store = get_default_credentials_store()
    store.delete(channel_id, provider_name)
    return {"channel_id": channel_id, "provider_name": provider_name, "status": "eliminado"}