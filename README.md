# descuenbot 🛒

Web app que centraliza los descuentos bancarios en supermercados argentinos.
Consultá rápido qué banco usar y en qué sucursal comprar para ahorrar hoy.

## ¿Por qué existe esto?

Los bancos publican sus descuentos por separado, en distintas apps y webs.
descuenbot los consolida en un solo lugar de consulta rápida desde el browser.

---

## Funcionalidades

### Web App

Interfaz visual para explorar los descuentos scrapeados. Filtrá por supermercado y día de la semana. Al hacer click en una card se abre un panel con todos los detalles.

```bash
uvicorn web:app --reload --port 8000
# → http://localhost:8000
```

### Scrapers

| Scraper | Fuente |
|---|---|
| `scraper_carrefour.py` | carrefour.com.ar/descuentos-bancarios |
| `scraper_dia.py` | diaonline.supermercadosdia.com.ar/medios-de-pago-y-promociones |

Cada scraper extrae banco, porcentaje, método de pago, tope, días de vigencia y formato de tienda, y guarda los resultados en `descuentos.db` (SQLite).

```bash
# Correr ambos scrapers en secuencia
python scrape_all.py

# O individualmente
python scraper_carrefour.py
python scraper_dia.py
```

### Bot de Telegram (opcional)

| Comando | Descripción |
|---|---|
| `/start` | Bienvenida y lista de bancos disponibles |
| `/hoy` | Descuentos vigentes hoy según el día de la semana |
| `/banco [nombre]` | Descuentos de un banco específico. Ej: `/banco galicia` |
| `/super [nombre]` | Descuentos en un supermercado específico. Ej: `/super carrefour` |

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Scraper | Playwright (Chromium headless) |
| Web backend | FastAPI + uvicorn |
| Web frontend | HTML + Tailwind CSS CDN + JS vanilla |
| Base de datos | SQLite (`descuentos.db`) |
| Hosting | Railway |
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
TOKEN=tu_token_de_telegram   # solo necesario para el bot
```

### 4. Scrapeá los datos

```bash
python scrape_all.py
```

Esto crea `descuentos.db` en la raíz del proyecto con todos los descuentos.

### 5. Levantá la web app

```bash
uvicorn web:app --reload --port 8000
```

Abrí `http://localhost:8000`.

---

## Ver los datos scrapeados

Para inspeccionar `descuentos.db` visualmente, usá [DB Browser for SQLite](https://sqlitebrowser.org/dl/):

1. Instalarlo
2. Abrir el archivo `descuentos.db` de la carpeta del proyecto
3. Ir a la pestaña **Browse Data** → tabla `descuentos`

---

## Variables de entorno en producción (Railway)

| Variable | Descripción |
|---|---|
| `TOKEN` | Token de Telegram (solo para bot.py) |

La base de datos SQLite persiste en un **Railway Volume** montado en el directorio del proyecto.

---

## Roadmap

- [x] v0.1 — Bot funcional con datos hardcodeados
- [x] v0.2 — Datos conectados a Google Sheets + deploy en Railway
- [x] v0.3 — Comando `/super` por supermercado
- [x] v0.4 — Scraper automático de Carrefour (Playwright + VTEX)
- [x] v0.5 — Web app con cards filtrables y modal de detalle
- [x] v0.6 — Scraper de Supermercados Día + migración a SQLite
- [ ] v1.0 — Cobertura completa de bancos y supermercados

---

## Autor

Desarrollado por [@COCOLICH3](https://github.com/COCOLICH3)
