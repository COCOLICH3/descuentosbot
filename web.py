"""
Web app de visualización de descuentos — Supermercados Argentina
Uso: uvicorn web:app --reload --port 8000
"""
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from db import get_all_descuentos

app = FastAPI(title="descuenbot")

CACHE_TTL = 300  # 5 minutos

_cache_data: list[dict] = []
_cache_ts: float = 0.0


def get_descuentos() -> list[dict]:
    global _cache_data, _cache_ts
    if time.monotonic() - _cache_ts > CACHE_TTL:
        _cache_data = get_all_descuentos()
        _cache_ts = time.monotonic()
    return _cache_data


TEMPLATES = Path(__file__).parent / "templates"


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(TEMPLATES / "v3.html")


@app.get("/api/descuentos")
def api_descuentos():
    return JSONResponse(content=get_descuentos())
