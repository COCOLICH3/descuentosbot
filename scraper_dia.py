"""
Scraper de descuentos bancarios — Supermercados Día Argentina
Uso: python scraper_dia.py
Escribe los resultados en descuentos.db (SQLite).
"""
import asyncio
import json
import os
import re
from datetime import datetime

import httpx
from playwright.async_api import async_playwright

from db import save_descuentos

LOGO_CACHE_FILE = "dia_logo_cache.json"
_logo_cache: dict[str, str] = {}


def _load_logo_cache():
    global _logo_cache
    if os.path.exists(LOGO_CACHE_FILE):
        with open(LOGO_CACHE_FILE, encoding="utf-8") as f:
            _logo_cache = json.load(f)


def _save_logo_cache():
    with open(LOGO_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(_logo_cache, f, ensure_ascii=False, indent=2)


def identificar_banco_por_logo(img_url: str) -> str:
    """Busca el banco en el cache local. Si no está, descarga la imagen para
    identificación manual y agrega una entrada vacía en el cache."""
    if not img_url:
        return "Sin datos"

    if img_url in _logo_cache:
        return _logo_cache[img_url] or "Sin datos"

    # Logo nuevo: descargar y guardar para identificación manual
    try:
        os.makedirs("logos_sin_identificar", exist_ok=True)
        resp = httpx.get(img_url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        ext = ".png" if "png" in resp.headers.get("content-type", "") else ".webp"
        img_hash = img_url.split("/")[-1].split("___")[-1].split(".")[0]
        img_path = f"logos_sin_identificar/{img_hash}{ext}"
        with open(img_path, "wb") as f:
            f.write(resp.content)
        # Agrega entrada vacía en el cache para que el usuario la complete
        _logo_cache[img_url] = ""
        _save_logo_cache()
        print(f"    ? Logo nuevo guardado: {img_path}")
    except Exception as e:
        print(f"    ⚠️  No se pudo descargar el logo: {e}")

    return "Sin datos"

URL = "https://diaonline.supermercadosdia.com.ar/medios-de-pago-y-promociones"
HEADERS = ["banco", "supermercado", "dia", "descuento", "tope", "metodo_pago", "vigencia", "canal", "promocion"]

# Bancos/billeteras donde el nombre = método de pago
BILLETERAS = {"Mercado Pago", "Uala", "Personal Pay", "Claro Pay", "MODO", "Cuenta DNI"}

BANCOS_CONOCIDOS = [
    # Strings más largos primero para evitar falsos positivos
    "mercado pago", "mercadopago",
    "banco de la ciudad", "banco ciudad",
    "banco de la nación", "banco de la nacion", "banco nación", "banco nacion",
    "banco provincia", "banco de la provincia",
    "banco patagonia",
    "banco galicia", "galicia",
    "banco santander", "santander",
    "banco macro", "macro",
    "banco supervielle", "supervielle",
    "banco columbia",
    "personal pay", "claro pay",
    "naranja x", "naranja",
    "hsbc", "bbva", "icbc", "brubank", "uala",
    "frances", "francés",
    "cuenta dni",
    "modo",
    "anses",
]

DIAS_NORMALIZADOS = {
    "lunes": "Lunes", "martes": "Martes",
    "miércoles": "Miercoles", "miercoles": "Miercoles",
    "jueves": "Jueves", "viernes": "Viernes",
    "sábado": "Sabado", "sabado": "Sabado",
    "domingo": "Domingo",
}

# ---------------------------------------------------------------------------
# Base de datos
# ---------------------------------------------------------------------------

def save_to_db(rows: list[list]):
    dicts = [dict(zip(HEADERS, r)) for r in rows]
    # Rellenar campo 'tipo_mercado' que no existe en Día
    for d in dicts:
        d.setdefault("tipo_mercado", None)
    save_descuentos(dicts, "Dia")


# ---------------------------------------------------------------------------
# Parsing del texto legal
# ---------------------------------------------------------------------------

def _extraer_banco(texto: str) -> str:
    t = texto.lower()
    for b in BANCOS_CONOCIDOS:
        if b in t:
            return b.replace("nación", "Nacion").title()
    return "Sin datos"


def _extraer_dias(texto: str) -> str:
    """Extrae los días de la semana del texto legal."""
    t = texto.lower()
    if "todos los días" in t or "todos los dias" in t:
        return "Todos los dias"
    encontrados = []
    for dia_raw, dia_norm in DIAS_NORMALIZADOS.items():
        if dia_raw in t and dia_norm not in encontrados:
            encontrados.append(dia_norm)
    if encontrados:
        return "/".join(encontrados)
    # Sin día específico: buscar rango de fechas como fallback
    # Acepta texto entre la fecha y "al" (ej: "01/04/2026 00:01 al 30/04/2026")
    m = re.search(
        r'(\d{1,2}/\d{1,2}/\d{4})[^/\n]{0,15}?\bal\b[^/\n]{0,10}?(\d{1,2}/\d{1,2}/\d{4})',
        texto, re.IGNORECASE
    )
    if m:
        return f"{m.group(1)} al {m.group(2)}"
    # Fecha única
    m2 = re.search(r'\d{1,2}/\d{1,2}/\d{4}', texto)
    if m2:
        return m2.group(0)
    return "Sin datos"


def _extraer_descuento(texto: str) -> str:
    # Porcentaje: "25%", "25 % dto"
    m = re.search(r'(\d+)\s*%', texto)
    if m:
        return f"{m.group(1)}%"
    # Cuotas sin interés: "3CSI", "3 CSI", "3 cuotas sin interés", "hasta 3 cuotas"
    m2 = re.search(r'(\d+)\s*(?:csi|cuotas?\s+sin\s+inter[eé]s)', texto, re.IGNORECASE)
    if m2:
        return f"{m2.group(1)} cuotas sin interés"
    return "Sin datos"


def _extraer_tope(texto: str) -> str:
    # "Tope : $10.000" del subtítulo, o "LÍMITE DE DESCUENTO ... $ 10000" del legal
    m = re.search(r'tope\s*[:\s]*\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    if m:
        return f"${m.group(1)}"
    m2 = re.search(r'l[íi]mite\s+de\s+descuento[^$]*\$\s*([\d.,]+)', texto, re.IGNORECASE)
    if m2:
        return f"${m2.group(1)}"
    return "Sin tope"


def _extraer_vigencia(texto: str) -> str:
    DATE = r'\d{1,2}/\d{1,2}/\d{4}'
    # "del 01/04/2026 ... al 30/04/2026" (con posible hora entre medio)
    m = re.search(
        rf'del\s+({DATE})[^/\n]{{0,15}}?\bal\b[^/\n]{{0,10}}?({DATE})',
        texto, re.IGNORECASE
    )
    if m:
        return f"{m.group(1)} al {m.group(2)}"
    # "01/04/2026 al 30/04/2026" (sin "del")
    m = re.search(
        rf'({DATE})[^/\n]{{0,15}}?\bal\b[^/\n]{{0,10}}?({DATE})',
        texto, re.IGNORECASE
    )
    if m:
        return f"{m.group(1)} al {m.group(2)}"
    # "hasta el 30/04/2026"
    m = re.search(rf'hasta\s+el\s+({DATE})', texto, re.IGNORECASE)
    if m:
        return m.group(1)
    # fecha sola: "MARTES 10/03/2026" o cualquier fecha única
    m = re.search(rf'({DATE})', texto)
    if m:
        return m.group(1)
    return "Sin datos"


def _extraer_metodo_pago(texto: str) -> str:
    t = texto.lower()
    tiene_debito  = "débito" in t or "debito" in t
    tiene_credito = "crédito" in t or "credito" in t
    if tiene_debito and tiene_credito:
        return "Débito y Crédito"
    if tiene_debito:
        return "Débito"
    if tiene_credito:
        return "Crédito"
    if "prepaga" in t:
        return "Prepaga"
    if "billetera" in t or "qr" in t:
        return "Billetera/QR"
    if "visa" in t or "mastercard" in t or "maestro" in t:
        return "Tarjeta"
    return "Sin datos"


# ---------------------------------------------------------------------------
# Modal de legales
# ---------------------------------------------------------------------------

MODAL_SELECTOR: str | None = None  # se descubre en la primera apertura

async def _leer_legal(page, card) -> str:
    """Hace click en 'Ver Legales', lee el texto del modal y lo cierra."""
    global MODAL_SELECTOR
    try:
        btn = card.locator('[class*="bank-modal__button"]')
        await btn.click()
        await page.wait_for_timeout(700)

        if MODAL_SELECTOR:
            # Selector ya conocido
            try:
                el = page.locator(MODAL_SELECTOR).last
                texto = await el.inner_text(timeout=3000)
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(300)
                return texto.strip()
            except Exception:
                pass

        # Primera vez: descubrir el selector probando candidatos
        candidatos = [
            '[class*="bank-modal__content"]',
            '[class*="bank-modal__text"]',
            '[class*="bank-modal__body"]',
            '[class*="bank-modal__container"]',
            '[class*="modal-layout__content"]',
            '[class*="modal-layout"]',
            '[role="dialog"]',
        ]
        for sel in candidatos:
            try:
                el = page.locator(sel).last
                if await el.is_visible(timeout=1500):
                    texto = await el.inner_text(timeout=2000)
                    if len(texto.strip()) > 20:
                        MODAL_SELECTOR = sel
                        print(f"    [modal selector: {sel}]")
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
                        return texto.strip()
            except Exception:
                continue

        # Si ningún selector funcionó, capturar el HTML del modal para debug
        await page.screenshot(path="debug_dia_modal.png")
        print("    ⚠️  No se encontró el selector del modal — ver debug_dia_modal.png")
        await page.keyboard.press("Escape")
        await page.wait_for_timeout(300)

    except Exception as e:
        print(f"    ⚠️  Error abriendo modal: {e}")

    return ""


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

async def scrape() -> list[list]:
    _load_logo_cache()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
            locale="es-AR",
        )
        page = await context.new_page()

        print(f"Abriendo {URL} ...")
        try:
            await page.goto(URL, wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"⚠️  Error al cargar la página: {e}")
            await browser.close()
            return []

        await page.wait_for_timeout(3000)

        # Scrollear hacia abajo para activar lazy-load del componente VTEX
        print("Scrolleando para cargar el contenido...")
        for _ in range(6):
            await page.evaluate("window.scrollBy(0, 600)")
            await page.wait_for_timeout(500)
        await page.evaluate("window.scrollTo(0, 0)")
        await page.wait_for_timeout(2000)

        # Esperar a que aparezcan las cards
        try:
            await page.wait_for_selector('[class*="list-by-days__item"]', timeout=20000)
            print("Cards detectadas.")
        except Exception:
            print("⚠️  No se detectaron cards. Guardando debug...")
            await page.screenshot(path="debug_dia.png", full_page=True)
            with open("debug_dia.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            print("   → Revisá debug_dia.png y debug_dia.html")
            await browser.close()
            return []

        # Verificar si "Todos" contiene todas las cards
        btn_todos = page.locator('[class*="list-by-days__button"]', has_text="Todos").first
        await btn_todos.click()
        await page.wait_for_timeout(800)
        count_todos = await page.locator('[class*="list-by-days__item"]').count()

        # Contar cards sumando todos los días individualmente
        day_buttons = page.locator('[class*="list-by-days__button"]')
        labels_dias = []
        for i in range(await day_buttons.count()):
            label = (await day_buttons.nth(i).inner_text()).strip()
            if label != "Todos":
                labels_dias.append(label)

        count_por_dia = 0
        for label in labels_dias:
            btn = page.locator('[class*="list-by-days__button"]', has_text=label).first
            await btn.click()
            await page.wait_for_timeout(600)
            n = await page.locator('[class*="list-by-days__item"]').count()
            count_por_dia += n
            print(f"  {label}: {n} cards")

        print(f"\nTodos: {count_todos} cards | Suma por días: {count_por_dia} cards")

        # Usar "Todos" si tiene la misma cantidad que la suma (sin duplicados entre días)
        # o si tiene más (ya deduplica internamente). Si tiene menos, iterar por días.
        usar_todos = count_todos >= count_por_dia // 2

        if usar_todos:
            print("→ Usando tab 'Todos' (extrae día del texto legal)")
            await btn_todos.click()
            await page.wait_for_timeout(800)
            tabs_a_iterar = [("Todos", None)]
        else:
            print("→ Iterando por cada día")
            tabs_a_iterar = [(label, label) for label in labels_dias]

        promos: dict[tuple, dict] = {}

        for tab_label, dia_fijo in tabs_a_iterar:
            if dia_fijo:
                btn = page.locator('[class*="list-by-days__button"]', has_text=tab_label).first
                await btn.click()
                await page.wait_for_timeout(800)

            cards = page.locator('[class*="list-by-days__item"]')
            total = await cards.count()
            print(f"\n→ Tab '{tab_label}': {total} cards")

            for i in range(total):
                card = cards.nth(i)
                print(f"  [{i+1}/{total}]", end=" ", flush=True)

                try:
                    titulo = (await card.locator('[class*="first-text"]').inner_text()).strip()
                except Exception:
                    titulo = ""
                try:
                    subtitulo = (await card.locator('[class*="second-text"]').inner_text()).strip()
                except Exception:
                    subtitulo = ""
                try:
                    fecha_card = (await card.locator('[class*="third-text"]').inner_text()).strip()
                except Exception:
                    fecha_card = ""

                flags = []
                flag_els = card.locator('[class*="flags-container"] p')
                for j in range(await flag_els.count()):
                    flags.append((await flag_els.nth(j).inner_text()).strip())
                canal = " / ".join(flags) if flags else "Sin datos"

                try:
                    img_src = await card.locator('[class*="img-logo"]').get_attribute("src") or ""
                except Exception:
                    img_src = ""

                legal_text = await _leer_legal(page, card)

                texto_todo = f"{titulo} {subtitulo} {fecha_card} {legal_text}"

                # Día: desde el tab si iteramos por día, sino desde el texto legal
                if dia_fijo:
                    dia_norm = DIAS_NORMALIZADOS.get(dia_fijo.lower(), dia_fijo)
                else:
                    dia_norm = _extraer_dias(texto_todo)

                clave = (titulo, subtitulo, canal)

                if clave in promos:
                    # Acumular días si es iteración por día
                    if dia_fijo:
                        dias_acum = promos[clave]["dia"].split("/")
                        if dia_norm not in dias_acum:
                            dias_acum.append(dia_norm)
                            promos[clave]["dia"] = "/".join(dias_acum)
                else:
                    # Banco: solo desde el texto visible de la card (no legal text — tiene demasiado ruido)
                    # Prioridad: logo cache → texto card → Sin datos
                    banco_desde_logo = _logo_cache.get(img_src, "")
                    banco_desde_texto = _extraer_banco(f"{titulo} {subtitulo}")
                    if banco_desde_logo:
                        banco = banco_desde_logo
                    elif banco_desde_texto != "Sin datos":
                        banco = banco_desde_texto
                    else:
                        banco = identificar_banco_por_logo(img_src)  # descarga img si es nueva

                    # Normalizar nombre
                    if banco.lower() == "naranja":
                        banco = "Naranja X"

                    descuento = _extraer_descuento(titulo) or _extraer_descuento(legal_text)
                    tope      = _extraer_tope(f"{subtitulo} {legal_text}")
                    metodo    = _extraer_metodo_pago(f"{subtitulo} {fecha_card} {legal_text}")
                    # Si el banco es una billetera digital, es también el método de pago
                    if banco in BILLETERAS and metodo == "Sin datos":
                        metodo = banco
                    vig_card  = _extraer_vigencia(fecha_card)
                    vigencia  = vig_card if vig_card != "Sin datos" else _extraer_vigencia(legal_text)

                    print(f"{banco} | {dia_norm} | {descuento}")

                    promos[clave] = {
                        "banco": banco, "img_src": img_src, "dia": dia_norm,
                        "descuento": descuento, "tope": tope, "metodo_pago": metodo,
                        "vigencia": vigencia, "canal": canal, "promocion": titulo,
                    }

        await page.screenshot(path="debug_dia.png", full_page=True)
        await browser.close()

        filas = []
        for datos in promos.values():
            print(f"  {datos['banco']:20} | {datos['dia']:25} | {datos['descuento']:8} | {datos['tope']}")
            filas.append([
                datos["banco"], "Dia", datos["dia"], datos["descuento"],
                datos["tope"], datos["metodo_pago"], datos["vigencia"],
                datos["canal"], datos["promocion"],
            ])

    return filas


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"=== Scraper Día — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    rows = asyncio.run(scrape())

    if not rows:
        print("No se encontraron datos.")
        return

    print(f"\nDescuentos encontrados: {len(rows)}")
    col_w = 16
    print("  ".join(h.ljust(col_w) for h in HEADERS))
    print("  ".join(["-" * col_w] * len(HEADERS)))
    for r in rows:
        print("  ".join(str(c).ljust(col_w) for c in r))

    print()
    save_to_db(rows)


if __name__ == "__main__":
    main()
