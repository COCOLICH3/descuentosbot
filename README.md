# DescuentoBot 🛒

Bot de Telegram + web app que centraliza los descuentos bancarios en supermercados argentinos.
Consultá rápido qué banco usar y en qué sucursal comprar para ahorrar hoy.

## ¿Por qué existe esto?

Los bancos publican sus descuentos por separado, en distintas apps y webs.
DescuentoBot los consolida en un solo lugar de consulta rápida, tanto desde Telegram como desde el browser.

---

## Funcionalidades

### Bot de Telegram

| Comando | Descripción |
|---|---|
| `/start` | Bienvenida y lista de bancos disponibles |
| `/hoy` | Descuentos vigentes hoy según el día de la semana |
| `/banco [nombre]` | Descuentos de un banco específico. Ej: `/banco galicia` |
| `/super [nombre]` | Descuentos en un supermercado específico. Ej: `/super carrefour` |

### Scraper de Carrefour

Levanta automáticamente los descuentos bancarios publicados en carrefour.com.ar y los guarda en Google Sheets. Extrae banco, porcentaje, método de pago, tope, días de vigencia y formato de tienda (Hiper / Maxi / Market / Express / Online).

```bash
python scraper_carrefour.py
```

### Web App

Interfaz visual para explorar los descuentos scrapeados. Muestra cards filtrables por día y formato de tienda. Al hacer click en una card se abre un panel con todos los detalles.

```bash
uvicorn web:app --reload --port 8000
# → http://localhost:8000
```

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Bot | python-telegram-bot v22 |
| Scraper | Playwright (Chromium headless) |
| Web backend | FastAPI + uvicorn |
| Web frontend | HTML + Tailwind CSS CDN + JS vanilla |
| Base de datos | Google Sheets via gspread |
| Hosting | Railway (worker process) |
| Lenguaje | Python 3.12+ |

---

## Cómo correrlo localmente

### 1. Cloná el repositorio

```bash
git clone https://github.com/COCOLICH3/descuentobot.git
cd descuentobot
```

### 2. Creá el entorno virtual e instalá dependencias

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
playwright install chromium
```

### 3. Configurá las variables de entorno

Creá un archivo `.env` en la raíz:

```
TOKEN=tu_token_de_telegram
```

Agregá también tu archivo `credentials.json` de Google Cloud (ver sección abajo).

### 4. Corré lo que necesites

```bash
# Bot de Telegram
python bot.py

# Scraper de Carrefour (actualiza Google Sheets)
python scraper_carrefour.py

# Web app (requiere haber scrapeado antes)
uvicorn web:app --reload --port 8000
```

---

## Configuración de Google Sheets

1. Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar **Google Sheets API** y **Google Drive API**
3. Crear una cuenta de servicio y descargar las credenciales como `credentials.json`
4. Compartir la planilla `descuentosbot` con el `client_email` del archivo de credenciales
5. La planilla principal (`sheet1`) debe tener estas columnas:

| banco | supermercado | dia | descuento | tope | metodo_pago |
|---|---|---|---|---|---|

> ⚠️ Los días deben escribirse sin tildes: `Miercoles`, no `Miércoles`.

El scraper escribe en una hoja separada llamada `carrefour_scrapeado` con columnas adicionales: `tipo_mercado`, `vigencia`, `promocion`.

---

## Variables de entorno en producción (Railway)

En lugar de `credentials.json`, el bot lee las credenciales de Google desde variables de entorno individuales:

| Variable | Descripción |
|---|---|
| `TOKEN` | Token de Telegram (BotFather) |
| `GOOGLE_PROJECT_ID` | ID del proyecto en Google Cloud |
| `GOOGLE_PRIVATE_KEY_ID` | ID de la clave privada |
| `GOOGLE_PRIVATE_KEY` | Clave privada completa (con `\n` literales) |
| `GOOGLE_CLIENT_EMAIL` | Email de la cuenta de servicio |
| `GOOGLE_CLIENT_ID` | ID del cliente |

> El archivo `test.py` es un helper para convertir `credentials.json` al formato de env vars que usa Railway.

---

## Roadmap

- [x] v0.1 — Bot funcional con datos hardcodeados
- [x] v0.2 — Datos conectados a Google Sheets + deploy en Railway
- [x] v0.3 — Comando `/super` por supermercado
- [x] v0.4 — Scraper automático de Carrefour (Playwright + VTEX)
- [x] v0.5 — Web app con cards filtrables y modal de detalle
- [ ] v0.6 — Más supermercados (Coto, Día, Jumbo)
- [ ] v1.0 — Cobertura completa de bancos y supermercados

---

## Autor

Desarrollado por [@COCOLICH3](https://github.com/COCOLICH3)
