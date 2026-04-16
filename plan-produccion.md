# Plan de Producción — descuenbot

## Contexto

La app está funcionando bien localmente. El objetivo es llevarla a producción para que cualquier persona pueda usarla online, con los scrapers corriendo automáticamente (sin intervención manual) al menos una vez por semana.

Hay tres desafíos técnicos principales:
1. **Playwright/Chromium** es pesado (~300MB) y necesita configuración especial en la nube
2. **SQLite** necesita almacenamiento persistente (un archivo en disco que no se borre con cada deploy)
3. **Los scrapers** necesitan correr en un horario programado automáticamente

---

## Opciones recomendadas

### Opción A — Railway ⭐ RECOMENDADA (ya lo usás, ~$5/mes)

Railway soporta todo lo necesario de forma integrada.

**Componentes:**

| Componente | Qué es | Costo |
|---|---|---|
| Web Service | Corre el servidor FastAPI | ~$3/mes (Hobby) |
| Volume | Disco persistente para `descuentos.db` | $0.25/GB/mes |
| Cron Service | Corre los scrapers automáticamente | ~$1/mes |

**Pasos:**

1. **Arreglar el Procfile** (actualmente apunta al bot de Telegram):
   ```
   web: uvicorn web:app --host 0.0.0.0 --port $PORT
   ```

2. **Agregar `nixpacks.toml`** para que Railway instale Chromium:
   ```toml
   [phases.setup]
   nixPkgs = ["chromium"]

   [phases.install]
   cmds = ["pip install -r requirements.txt", "playwright install chromium", "playwright install-deps chromium"]
   ```

3. **Crear un Volume en Railway** y montarlo en `/app`. Esto garantiza que `descuentos.db` persiste entre deploys.

4. **Agregar un Cron Service** en Railway apuntando al mismo repo con el comando:
   ```
   python scrape_all.py
   ```
   - 1x por semana: `0 6 * * 1` (lunes a las 6am)
   - 1x por día: `0 6 * * *`

5. **Variables de entorno** en Railway Dashboard: solo `TOKEN` si se quiere usar el bot.

**Costo estimado: ~$5-8/mes** en plan Hobby.

---

### Opción B — Oracle Cloud Free Tier ⭐ COSTO CERO (gratis para siempre)

Oracle ofrece VMs ARM gratuitas permanentes con **4 OCPUs y 24GB RAM total**.

**Setup en una VM Ubuntu ARM:**

```bash
# 1. Instalar dependencias del sistema
sudo apt update && sudo apt install -y python3-pip python3-venv nginx

# 2. Clonar el repo
git clone https://github.com/COCOLICH3/descuentobot.git
cd descuentobot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium

# 3. Correr scrapers la primera vez para poblar la DB
python scrape_all.py

# 4. Crear servicio systemd para que el servidor arranque solo
sudo nano /etc/systemd/system/descuenbot.service
```

```ini
[Unit]
Description=descuenbot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/descuentobot
ExecStart=/home/ubuntu/descuentobot/venv/bin/uvicorn web:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable descuenbot
sudo systemctl start descuenbot

# 5. nginx como reverse proxy (puerto 80 → 8000)
sudo nano /etc/nginx/sites-available/descuenbot
```

```nginx
server {
    listen 80;
    server_name TU_IP_O_DOMINIO;
    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/descuenbot /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# 6. Programar scrapers con crontab (1x por semana, lunes 6am)
crontab -e
# Agregar esta línea:
0 6 * * 1 cd /home/ubuntu/descuentobot && source venv/bin/activate && python scrape_all.py >> /var/log/scraper.log 2>&1
```

**Costo: $0/mes** (garantizado gratis para siempre por Oracle)
**Contra**: Requiere ~1 hora de setup manual.

---

### Opción C — Render (gratis con limitaciones, NO recomendada para uso real)

- Web service gratuito pero **se duerme después de 15 minutos** de inactividad
- La primera visita después del sleep tarda ~30 segundos en cargar
- Cron jobs disponibles en plan gratuito
- Playwright requiere Docker

**No recomendada** salvo para pruebas.

---

## El problema de Playwright en la nube

Playwright necesita Chromium instalado en el servidor. En todos los casos hay que correr:

```bash
playwright install chromium
playwright install-deps chromium
```

En Railway esto se hace automáticamente con el `nixpacks.toml`. En VPS se hace una sola vez al configurar el servidor.

---

## Frecuencia de scraping recomendada

| Frecuencia | Cuándo tiene sentido |
|---|---|
| 1x/semana (lunes) | Las promos cambian mensualmente → suficiente |
| 1x/día (6am) | Si hay cambios frecuentes → más fresco |
| 2x/semana (lunes y jueves) | Balance recomendado |

Cada ejecución tarda ~3-5 minutos. No es costosa.

---

## Archivos a crear/modificar para Railway

| Archivo | Cambio |
|---|---|
| `Procfile` | `web: uvicorn web:app --host 0.0.0.0 --port $PORT` |
| `nixpacks.toml` | Nuevo — instala Chromium en el build de Railway |

---

## Decisión

| Prioridad | Opción |
|---|---|
| Más simple y rápido | Railway (~$5-8/mes, ~30min de setup) |
| Costo cero permanente | Oracle Cloud Free Tier (~$0/mes, ~1h de setup) |
