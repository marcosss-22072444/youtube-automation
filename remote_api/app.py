"""app.py — FastAPI app del Remote API, con autenticacion por API key propia."""
from fastapi import FastAPI, Header, HTTPException, Depends
from core.config import settings

app = FastAPI(title="YouTube Automation Remote API")


def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.remote_api_key:
        raise HTTPException(status_code=401, detail="API key invalida")
    return True


from remote_api.routers import channels, schedules
app.include_router(channels.router, dependencies=[Depends(verify_api_key)])
app.include_router(schedules.router, dependencies=[Depends(verify_api_key)])