"""
Web app de visualización de descuentos — Carrefour Argentina
Uso: uvicorn web:app --reload --port 8000
"""
import time
from pathlib import Path

import gspread
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from scraper_carrefour import _build_creds

load_dotenv()

app = FastAPI(title="DescuentoBot Web")

SHEET_NAME = "carrefour_scrapeado"
CACHE_TTL = 300  # 5 minutos

_cache_data: list[dict] = []
_cache_ts: float = 0.0


def _fetch_from_sheets() -> list[dict]:
    creds = _build_creds()
    client = gspread.authorize(creds)
    ws = client.open("descuentosbot").worksheet(SHEET_NAME)
    return ws.get_all_records()


def get_descuentos() -> list[dict]:
    global _cache_data, _cache_ts
    if time.monotonic() - _cache_ts > CACHE_TTL:
        _cache_data = _fetch_from_sheets()
        _cache_ts = time.monotonic()
    return _cache_data


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse(Path(__file__).parent / "templates" / "index.html")


@app.get("/api/descuentos")
def api_descuentos():
    return JSONResponse(content=get_descuentos())
