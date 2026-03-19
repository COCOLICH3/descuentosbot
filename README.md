# DescuentoBot 🛒

Bot de Telegram que centraliza los descuentos bancarios en supermercados argentinos.
El usuario elige su banco y al instante sabe dónde comprar hoy para ahorrar.

## ¿Por qué existe esto?

Los bancos publican sus descuentos por separado, en distintas apps y webs.
DescuentoBot los consolida en un solo lugar de consulta rápida.

## Comandos disponibles

| Comando | Descripción |
|---|---|
| `/start` | Bienvenida y lista de comandos |
| `/hoy` | Descuentos disponibles hoy según el día de la semana |
| `/banco [nombre]` | Descuentos de un banco específico. Ej: `/banco galicia` |

## Stack técnico

- **Lenguaje:** Python 3.14
- **Librería:** python-telegram-bot v20+
- **Base de datos:** Google Sheets via gspread
- **Variables de entorno:** python-dotenv
- **Hosting:** Railway (24/7)

## Cómo correrlo localmente

1. Cloná el repositorio
```
   git clone https://github.com/tu-usuario/descuentobot.git
   cd descuentobot
```

2. Creá el entorno virtual e instalá dependencias
```
   python -m venv venv
   venv\Scripts\activate
   pip install python-telegram-bot python-dotenv gspread google-auth
```

3. Creá un archivo `.env` en la raíz con tu token
```
   TOKEN=tu_token_aca
```

4. Agregá tu archivo `credentials.json` de Google Cloud en la raíz
   (ver sección de configuración de Google Sheets abajo)

5. Corré el bot
```
   python bot.py
```

## Configuración de Google Sheets

1. Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com)
2. Habilitar **Google Sheets API** y **Google Drive API**
3. Crear una cuenta de servicio y descargar las credenciales como `credentials.json`
4. Compartir la planilla con el `client_email` del archivo de credenciales
5. La planilla debe tener estas columnas exactas:

| banco | supermercado | dia | descuento |
|---|---|---|---|
| galicia | Coto | Martes | 25% |

> ⚠️ Los días deben escribirse sin tildes: Miercoles, no Miércoles.

## Variables de entorno en producción (Railway)

En lugar de `credentials.json`, el bot lee las credenciales de Google desde variables de entorno individuales:

| Variable | Descripción |
|---|---|
| `TOKEN` | Token de Telegram (BotFather) |
| `GOOGLE_PROJECT_ID` | ID del proyecto en Google Cloud |
| `GOOGLE_PRIVATE_KEY_ID` | ID de la clave privada |
| `GOOGLE_PRIVATE_KEY` | Clave privada completa (con `\n`) |
| `GOOGLE_CLIENT_EMAIL` | Email de la cuenta de servicio |
| `GOOGLE_CLIENT_ID` | ID del cliente |

## Roadmap

- [x] v0.1 — Bot funcional con datos hardcodeados
- [x] v0.2 — Datos conectados a Google Sheets + deploy en Railway
- [ ] v0.3 — Recordatorios automáticos por usuario
- [ ] v1.0 — Cobertura completa de bancos y supermercados

## Autor

Desarrollado por [@COCOLICH3](https://github.com/COCOLICH3)

