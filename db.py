"""
Módulo de base de datos SQLite para descuenbot.
Tabla única 'descuentos' con todas las columnas de ambos scrapers.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "descuentos.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS descuentos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    banco        TEXT,
    supermercado TEXT,
    dia          TEXT,
    descuento    TEXT,
    tope         TEXT,
    metodo_pago  TEXT,
    vigencia     TEXT,
    promocion    TEXT,
    tipo_mercado TEXT,
    canal        TEXT,
    scrapeado_en TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript(_SCHEMA)


def save_descuentos(rows: list[dict], supermercado: str):
    """Reemplaza todos los registros de un supermercado con los nuevos datos."""
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM descuentos WHERE supermercado = ?", (supermercado,))
        conn.executemany(
            """INSERT INTO descuentos
               (banco, supermercado, dia, descuento, tope, metodo_pago, vigencia, promocion, tipo_mercado, canal)
               VALUES (:banco, :supermercado, :dia, :descuento, :tope, :metodo_pago, :vigencia, :promocion, :tipo_mercado, :canal)
            """,
            rows,
        )
    print(f"✅ {len(rows)} filas guardadas en SQLite para '{supermercado}'.")


def get_all_descuentos() -> list[dict]:
    init_db()
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM descuentos ORDER BY supermercado, banco").fetchall()
    return [dict(r) for r in rows]