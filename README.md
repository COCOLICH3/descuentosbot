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

## Bancos disponibles (v0.1)

- Galicia
- Santander
- BBVA
- Macro

## Stack técnico

- **Lenguaje:** Python 3.14
- **Librería:** python-telegram-bot v20+
- **Variables de entorno:** python-dotenv
- **Base de datos:** hardcodeada en el código (migración a Google Sheets en v0.2)

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
   pip install python-telegram-bot python-dotenv
```

3. Creá un archivo `.env` en la raíz con tu token
```
   TOKEN=tu_token_aca
```

4. Corré el bot
```
   python bot.py
```

## Roadmap

- [x] v0.1 — Bot funcional con datos hardcodeados
- [ ] v0.2 — Datos conectados a Google Sheets
- [ ] v0.3 — Recordatorios automáticos por usuario
- [ ] v1.0 — Deploy en Railway (24/7)

## Autor

Desarrollado por [@COCOLICH3](https://github.com/COCOLICH3)