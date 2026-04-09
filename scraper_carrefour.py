"""
Scraper de descuentos bancarios — Carrefour Argentina
Uso: python scraper_carrefour.py
Escribe los resultados en descuentos.db (SQLite).
"""
import asyncio
import re
from datetime import datetime

from playwright.async_api import async_playwright

from db import save_descuentos

URL = "https://www.carrefour.com.ar/descuentos-bancarios"
HEADERS = ["banco", "supermercado", "tipo_mercado", "dia", "descuento", "tope", "metodo_pago", "vigencia", "promocion"]

LOGO_CLASS_TO_TIPO = {
    "logoMaxi":    "Carrefour Maxi",
    "logoMarket":  "Carrefour Market",
    "logoExpress": "Carrefour Express",
    "logoBio":     "Carrefour Bio",
    "logoOnline":  "Carrefour Online",
    "logoMain":    "Carrefour",
}

BANCOS_CONOCIDOS = [
    "galicia", "santander", "bbva", "macro", "hsbc", "icbc",
    "ciudad", "nacion", "nación", "provincia", "patagonia", "supervielle",
    "naranja", "uala", "mercadopago", "mercado pago", "brubank", "bnp",
    "frances", "francés",
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
    # Rellenar campo 'canal' que no existe en Carrefour
    for d in dicts:
        d.setdefault("canal", None)
    save_descuentos(dicts, "Carrefour")


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _extraer_banco(text_lower: str) -> str:
    for b in BANCOS_CONOCIDOS:
        if b in text_lower:
            return b.replace("nación", "Nacion").title()
    return "Sin datos"


def _tipo_mercado_desde_logos(logo_classes: list[str]) -> str:
    """Convierte las clases CSS de los logos al nombre del tipo de mercado."""
    if not logo_classes:
        return "Carrefour"
    tipos = []
    for cls in logo_classes:
        if cls in LOGO_CLASS_TO_TIPO:
            tipos.append(LOGO_CLASS_TO_TIPO[cls])
    return "/".join(tipos) if tipos else "Carrefour"


def _extraer_dia(text_lower: str) -> str:
    if "todos los días" in text_lower or "todos los dias" in text_lower:
        return "Todos los dias"
    encontrados = []
    for dia_raw, dia_norm in DIAS_NORMALIZADOS.items():
        if dia_raw in text_lower and dia_norm not in encontrados:
            encontrados.append(dia_norm)
    return "/".join(encontrados) if encontrados else "Sin datos"


def _extraer_descuento(text: str) -> str:
    # Busca patrones como "25%", "25 % de descuento", "hasta 30%"
    m = re.search(r'(\d+)\s*%', text)
    return f"{m.group(1)}%" if m else "Sin datos"


def _extraer_tope(text: str) -> str:
    # "Tope de devolución $10.000", "tope: $5.000", "máximo $3.000"
    # Permite palabras entre la keyword y el signo $, pero requiere $ antes del número
    m = re.search(
        r'(?:tope|máximo|maximo|reintegro\s+de)[\w\sáéíóúüÁÉÍÓÚ:]{0,30}?\$\s*([\d.,]+)',
        text, re.IGNORECASE
    )
    if m:
        return f"${m.group(1)}"
    # "hasta $X" — requiere $ explícito para no confundir con "hasta 3 cuotas"
    m2 = re.search(r'hasta\s+\$\s*([\d.,]+)', text, re.IGNORECASE)
    if m2:
        return f"${m2.group(1)}"
    m3 = re.search(r'límite[:\s]*\$\s*([\d.,]+)', text, re.IGNORECASE)
    return f"${m3.group(1)}" if m3 else "Sin tope"


def _extraer_metodo_pago(text_lower: str) -> str:
    if "débito" in text_lower or "debito" in text_lower:
        if "crédito" in text_lower or "credito" in text_lower:
            return "Débito y Crédito"
        return "Débito"
    if "crédito" in text_lower or "credito" in text_lower:
        return "Crédito"
    if "prepaga" in text_lower:
        return "Prepaga"
    if "billetera" in text_lower or "qr" in text_lower:
        return "Billetera/QR"
    return "Sin datos"


_MESES = r'(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)'

def _extraer_vigencia(text: str) -> str:
    patrones = [
        r'hasta el \d{1,2} de ' + _MESES,
        r'\d{1,2}[/\-]\d{1,2}(?:[/\-]\d{2,4})?\s+(?:al|a)\s+\d{1,2}[/\-]\d{1,2}',
        # "lunes y miércoles de abril" — usa mes explícito para no capturar "AbrilComprando"
        r'(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?)'
        r'(?:\s*[y,]\s*(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bados?|domingos?))*'
        r'(?:\s+de\s+' + _MESES + r'|\s+\d{1,2}\s+de\s+' + _MESES + r')',
        r'del \d{1,2} al \d{1,2} de ' + _MESES,
        r'todos los ' + _MESES,
    ]
    for pat in patrones:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return "Sin datos"


def parse_bloque(text: str, logo_classes: list[str] | None = None, promocion: str = "") -> dict | None:
    """Parsea un bloque de texto crudo y devuelve un dict con los campos."""
    text = text.strip()
    if not text or len(text) < 10:
        return None

    text_lower = text.lower()

    banco = _extraer_banco(text_lower)
    descuento = _extraer_descuento(text)

    # Si el texto principal no tiene datos, intentar extraerlos del título de la promoción
    if banco == "Sin datos" and promocion:
        banco = _extraer_banco(promocion.lower())
    metodo_pago = _extraer_metodo_pago(text_lower)
    if metodo_pago == "Sin datos" and promocion:
        metodo_pago = _extraer_metodo_pago(promocion.lower())

    # Descartar bloques sin información útil
    if banco == "Sin datos" and descuento == "Sin datos":
        return None

    return {
        "banco": banco,
        "supermercado": "Carrefour",
        "tipo_mercado": _tipo_mercado_desde_logos(logo_classes or []),
        "dia": _extraer_dia(text_lower),
        "descuento": descuento,
        "tope": _extraer_tope(text),
        "metodo_pago": metodo_pago,
        "vigencia": _extraer_vigencia(text),
        "promocion": promocion,
    }


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------

async def scrape() -> list[list]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"Abriendo {URL} ...")
        try:
            await page.goto(URL, wait_until="load", timeout=40000)
        except Exception as e:
            print(f"⚠️  Error al cargar la página: {e}")
            await browser.close()
            return []

        # Dar tiempo extra para que VTEX hidrate el contenido JS
        await page.wait_for_timeout(5000)

        # Esperar contenido dinámico de VTEX.
        # Si esto falla, revisá debug_carrefour.html para ver el selector correcto.
        SELECTOR_CONTENIDO = "[class*='cardBox']"
        try:
            await page.wait_for_selector(SELECTOR_CONTENIDO, timeout=15000)
        except Exception:
            print("⚠️  No se detectó contenido de descuentos. Guardando debug...")
            await page.screenshot(path="debug_carrefour.png", full_page=True)
            with open("debug_carrefour.html", "w", encoding="utf-8") as f:
                f.write(await page.content())
            print("   → Revisá debug_carrefour.png y debug_carrefour.html para ajustar los selectores.")
            await browser.close()
            return []

        # Extraer texto de cada bloque de descuento.
        # AJUSTAR el selector de 'bloques' si la estructura de la página cambia.
        bloques: list[dict] = await page.evaluate("""
        () => {
            const cards = document.querySelectorAll('[class*="cardBox"]');
            if (cards.length === 0) {
                const main = document.querySelector('main') || document.body;
                return [{ text: main.innerText, logo_classes: [] }];
            }
            return Array.from(cards).map(card => {
                // Los logos de "Comprando en:" tienen clase logoIcon + logoMain/logoMarket/etc.
                const logoEls = card.querySelectorAll('[class*="logoIcon"]');
                const logo_classes = Array.from(logoEls).flatMap(el => {
                    return Array.from(el.classList).filter(c =>
                        c.includes('logoMain') || c.includes('logoMarket') ||
                        c.includes('logoMaxi') || c.includes('logoExpress') ||
                        c.includes('logoOnline') || c.includes('logoBio')
                    ).map(c => c.split('-').pop()); // extrae "logoMain" de "valtech-...-0-x-logoMain"
                });
                const titleEl = card.querySelector('[class*="ColRightTittle"]');
                const promocion = titleEl ? (titleEl.textContent || titleEl.innerText || '').trim() : '';
                return { text: card.textContent, logo_classes, promocion };
            });
        }
        """)

        # Siempre guardar debug para inspeccionar selectores
        await page.screenshot(path="debug_carrefour.png", full_page=True)
        with open("debug_carrefour.html", "w", encoding="utf-8") as f:
            f.write(await page.content())
        print("   → debug_carrefour.png y debug_carrefour.html guardados.")

        await browser.close()

    filas = []
    vistos = set()
    for bloque in bloques:
        parsed = parse_bloque(bloque["text"], bloque.get("logo_classes", []), bloque.get("promocion", ""))
        if not parsed:
            continue
        clave = (parsed["banco"], parsed["tipo_mercado"], parsed["dia"], parsed["descuento"])
        if clave in vistos:
            continue
        vistos.add(clave)
        filas.append([parsed[col] for col in HEADERS])
    return filas


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"=== Scraper Carrefour — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    rows = asyncio.run(scrape())

    if not rows:
        print("No se encontraron datos para guardar.")
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
