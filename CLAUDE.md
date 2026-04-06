# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the bot locallyel
python bot.py

# Run test.py (utility to print credentials.json as JSON string, used for Railway setup)
python test.py
```

## Architecture

This is a single-file Telegram bot (`bot.py`) that fetches discount data from a Google Sheets spreadsheet on every command call — there is no local cache or database.

**Data flow:** User sends Telegram command → handler calls `get_descuentos()` → authenticates with Google via service account → fetches all rows from the `descuentosbot` Google Sheet → filters/formats in memory → replies to user.

**Google Sheets schema** (columns must match exactly):

| banco | supermercado | dia | descuento | tope | metodo_pago |
|---|---|---|---|---|---|

- `dia` supports slash-separated values (e.g., `Martes/Jueves`) and `"Todos los dias"`
- Days must be written without accent marks (e.g., `Miercoles`, not `Miércoles`)

**Bot commands registered in `main()`:**
- `/start` — welcome + dynamic list of available banks from the sheet
- `/hoy` — discounts for the current weekday (uses `DIAS_ES` dict to translate Python's English weekday names)
- `/banco <nombre>` — discounts for a specific bank
- `/super <nombre>` — discounts for a specific supermarket

## Environment variables

**Local:** uses `.env` file with `TOKEN` and Google credentials.

**Production (Railway):** credentials.json is not used — instead, individual env vars are read and assembled into a dict in `get_descuentos()`:

| Variable | Purpose |
|---|---|
| `TOKEN` | Telegram bot token |
| `GOOGLE_PROJECT_ID` | Google Cloud project ID |
| `GOOGLE_PRIVATE_KEY_ID` | Service account key ID |
| `GOOGLE_PRIVATE_KEY` | Private key (with literal `\n` which are replaced at runtime) |
| `GOOGLE_CLIENT_EMAIL` | Service account email |
| `GOOGLE_CLIENT_ID` | Service account client ID |

`test.py` is a helper script to parse `credentials.json` and print its contents as a flat JSON string, useful for copying values into Railway env vars.

## Deployment

Hosted on Railway as a worker process (not a web server). The `Procfile` defines: `worker: python bot.py`. The bot uses long polling (`run_polling()`), not webhooks.
