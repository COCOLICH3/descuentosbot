# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the web app locally
uvicorn web:app --reload --port 8000

# Run scrapers manually
python scraper_carrefour.py
python scraper_dia.py
```

## Architecture

FastAPI web app (`web.py`) that serves discount data scraped from supermarket websites.

**Data flow:** Scrapers write to `descuentos.db` (SQLite) → `web.py` reads from SQLite with a 5-minute in-memory cache → `/api/descuentos` endpoint → frontend (`templates/v2.html`)

**Database:** SQLite file `descuentos.db` in the project root. Managed via `db.py`. No external database needed.

**SQLite schema** (`descuentos` table):

| campo        | descripción                                 |
|---|---|
| banco        | Nombre del banco / billetera                |
| supermercado | Carrefour / Dia                             |
| dia          | Día(s) de la semana, slash-separated        |
| descuento    | Porcentaje (e.g. `25%`)                     |
| tope         | Tope de devolución (e.g. `$10.000`)         |
| metodo_pago  | Débito / Crédito / etc.                     |
| vigencia     | Período de vigencia                         |
| promocion    | Título de la promoción                      |
| tipo_mercado | Carrefour only: Maxi / Market / Express     |
| canal        | Día only: canal de venta                    |
| scrapeado_en | Timestamp de la última actualización        |

- `dia` supports slash-separated values (e.g., `Martes/Jueves`) and `"Todos los dias"`
- Days must be written without accent marks (e.g., `Miercoles`, not `Miércoles`)

## Scrapers

- `scraper_carrefour.py` — scrapes `carrefour.com.ar/descuentos-bancarios` using Playwright
- `scraper_dia.py` — scrapes `diaonline.supermercadosdia.com.ar/medios-de-pago-y-promociones` using Playwright

Each scraper deletes all existing rows for its supermarket and inserts fresh data on every run.

## Environment variables

Only `TOKEN` is needed if running the Telegram bot. No Google credentials required.

| Variable | Purpose |
|---|---|
| `TOKEN` | Telegram bot token (only for bot.py) |

## Deployment

Hosted on Railway as a web service. `web.py` runs via uvicorn. SQLite database persists via a Railway Volume mounted at the project directory.