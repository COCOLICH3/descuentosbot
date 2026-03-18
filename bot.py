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
    import json
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly",
              "https://www.googleapis.com/auth/drive.readonly"]
    
    google_creds = os.getenv("GOOGLE_CREDENTIALS")
    if google_creds:
        creds_dict = json.loads(google_creds)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scopes)
    
    client = gspread.authorize(creds)
    sheet = client.open("descuentosbot").sheet1
    datos = sheet.get_all_records()
    print("Datos leídos:", datos)
    return datos

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "👋 ¡Hola! Soy DescuentoBot.\n\n"
        "Te digo qué descuentos tenés hoy en supermercados según tu banco.\n\n"
        "📌 Comandos disponibles:\n"
        "/hoy — Ver todos los descuentos de hoy\n"
        "/banco [nombre] — Ver descuentos de tu banco\n"
        "   Ejemplo: /banco galicia\n\n"
        "🏦 Bancos disponibles: galicia, santander, bbva, macro"
    )
    await update.message.reply_text(texto)

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dia_hoy = DIAS_ES[datetime.now().strftime("%A")]
    registros = get_descuentos()

    resultado = f"📅 Descuentos para hoy ({dia_hoy}):\n\n"
    encontrados = False

    for row in registros:
        if row["dia"] == dia_hoy:
            resultado += f"🏦 {row['banco'].capitalize()} → {row['supermercado']} {row['descuento']}\n"
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
    bancos_disponibles = list(set(row["banco"] for row in registros))

    if nombre not in bancos_disponibles:
        await update.message.reply_text(
            f"❌ No encontré el banco '{nombre}'.\n"
            f"Bancos disponibles: {', '.join(bancos_disponibles)}"
        )
        return

    resultado = f"🏦 Descuentos de {nombre.capitalize()}:\n\n"
    for row in registros:
        if row["banco"] == nombre:
            resultado += f"📅 {row['dia']} → {row['supermercado']} {row['descuento']}\n"

    await update.message.reply_text(resultado)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("banco", banco))
    app.run_polling()

if __name__ == "__main__":
    main()
