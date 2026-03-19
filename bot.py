import logging
import os
import gspread
from google.oauth2.service_account import Credentials
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("TOKEN")

DIAS_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miercoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sabado", "Sunday": "Domingo"
}

logging.basicConfig(level=logging.INFO)

def get_descuentos():

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
              "https://www.googleapis.com/auth/drive.readonly"]
    
    creds_info = {
        "type": "service_account",
        "project_id": os.getenv("GOOGLE_PROJECT_ID"),
        "private_key_id": os.getenv("GOOGLE_PRIVATE_KEY_ID"),
        "private_key": os.getenv("GOOGLE_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.getenv("GOOGLE_CLIENT_EMAIL"),
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("descuentosbot").sheet1
    return sheet.get_all_records()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    registros = get_descuentos()
    bancos = sorted(set(row["banco"].lower() for row in registros))
    lista_bancos = "\n".join(f"   • {b}" for b in bancos)
    
    texto = (
        "👋 ¡Hola! Soy DescuentoBot.\n\n"
        "Te digo qué descuentos tenés hoy en supermercados según tu banco.\n\n"
        "📌 Comandos disponibles:\n"
        "/hoy — Ver todos los descuentos de hoy\n"
        "/banco [nombre] — Ver descuentos de tu banco\n"
        "/super [nombre] — Ver descuentos en un supermercado. Ej: /super carrefour\n"
        "   Ejemplo: /banco galicia\n\n"
        f"🏦 Bancos disponibles:\n{lista_bancos}"
    )
    await update.message.reply_text(texto)

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dia_hoy = DIAS_ES[datetime.now().strftime("%A")]
    registros = get_descuentos()

    resultado = f"📅 Descuentos para hoy ({dia_hoy}):\n\n"
    encontrados = False

    for row in registros:
        dias_fila = [d.strip() for d in row["dia"].split("/")]
        if dia_hoy in dias_fila or row["dia"] == "Todos los dias":
            resultado += f"🏦 {row['banco']} → {row['supermercado']}\n"
            resultado += f"   💸 {row['descuento']}"
            if row.get('tope') and row['tope'] != 'Sin tope':
                resultado += f" (tope {row['tope']})"
            resultado += f"\n   💳 {row['metodo_pago']}\n\n"
            encontrados = True

    if not encontrados:
        resultado = f"😔 No hay descuentos registrados para el {dia_hoy}."

    await update.message.reply_text(resultado)

async def banco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Escribí el nombre de tu banco.\nEjemplo: /banco galicia")
        return

    nombre = context.args[0].lower()
    registros = get_descuentos()
    bancos_disponibles = list(set(row["banco"].lower() for row in registros))

    if nombre not in bancos_disponibles:
        await update.message.reply_text(
            f"❌ No encontré el banco '{nombre}'.\n"
            f"Bancos disponibles: {', '.join(sorted(bancos_disponibles))}"
        )
        return

    resultado = f"🏦 Descuentos de {nombre.capitalize()}:\n\n"
    for row in registros:
        if row["banco"].lower() == nombre:
            resultado += f"🛒 {row['supermercado']} — {row['dia']}\n"
            resultado += f"   💸 {row['descuento']}"
            if row.get('tope') and row['tope'] != 'Sin tope':
                resultado += f" (tope {row['tope']})"
            resultado += f"\n   💳 {row['metodo_pago']}\n\n"

    await update.message.reply_text(resultado)

async def supermercado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ Escribí el nombre del supermercado.\n"
            "Ejemplo: /super carrefour\n\n"
            "🛒 Supermercados disponibles: carrefour, dia"
        )
        return

    nombre = context.args[0].lower()
    registros = get_descuentos()
    supers_disponibles = list(set(row["supermercado"].lower() for row in registros))

    if nombre not in supers_disponibles:
        await update.message.reply_text(
            f"❌ No encontré '{nombre}'.\n"
            f"Supermercados disponibles: {', '.join(sorted(supers_disponibles))}"
        )
        return

    resultado = f"🛒 Descuentos en {nombre.capitalize()}:\n\n"
    for row in registros:
        if row["supermercado"].lower() == nombre:
            resultado += f"🏦 {row['banco']} — {row['dia']}\n"
            resultado += f"   💸 {row['descuento']}"
            if row.get('tope') and row['tope'] != 'Sin tope':
                resultado += f" (tope {row['tope']})"
            resultado += f"\n   💳 {row['metodo_pago']}\n\n"

    await update.message.reply_text(resultado)   

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("banco", banco))
    app.add_handler(CommandHandler("super", supermercado))
    app.run_polling()

if __name__ == "__main__":
    main()
