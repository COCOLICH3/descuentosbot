import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# — Reemplazá esto con tu token —
TOKEN = "8258854543:AAF-rijvdfGO3_lrg0O5uCNtSvyrPIoBmbk"

# Base de datos de descuentos (por ahora hardcodeada, después va a Google Sheets)
DESCUENTOS = {
    "galicia": [
        {"super": "Coto", "dia": "Martes", "descuento": "25%"},
        {"super": "Carrefour", "dia": "Jueves", "descuento": "20%"},
    ],
    "santander": [
        {"super": "Jumbo", "dia": "Miércoles", "descuento": "30%"},
        {"super": "Disco", "dia": "Viernes", "descuento": "15%"},
    ],
    "bbva": [
        {"super": "Walmart", "dia": "Lunes", "descuento": "20%"},
        {"super": "Coto", "dia": "Viernes", "descuento": "25%"},
    ],
    "macro": [
        {"super": "La Anónima", "dia": "Miércoles", "descuento": "20%"},
        {"super": "Carrefour", "dia": "Sábado", "descuento": "15%"},
    ],
}

DIAS_ES = {
    "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
    "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
}

logging.basicConfig(level=logging.INFO)

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
    from datetime import datetime
    dia_hoy = DIAS_ES[datetime.now().strftime("%A")]
    
    resultado = f"📅 Descuentos para hoy ({dia_hoy}):\n\n"
    encontrados = False

    for banco, ofertas in DESCUENTOS.items():
        for o in ofertas:
            if o["dia"] == dia_hoy:
                resultado += f"🏦 {banco.capitalize()} → {o['super']} {o['descuento']}\n"
                encontrados = True

    if not encontrados:
        resultado = f"😔 No hay descuentos registrados para el {dia_hoy}."

    await update.message.reply_text(resultado)

async def banco(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Escribí el nombre de tu banco.\nEjemplo: /banco galicia")
        return

    nombre = context.args[0].lower()

    if nombre not in DESCUENTOS:
        await update.message.reply_text(
            f"❌ No encontré el banco '{nombre}'.\n"
            f"Bancos disponibles: {', '.join(DESCUENTOS.keys())}"
        )
        return

    resultado = f"🏦 Descuentos de {nombre.capitalize()}:\n\n"
    for o in DESCUENTOS[nombre]:
        resultado += f"📅 {o['dia']} → {o['super']} {o['descuento']}\n"

    await update.message.reply_text(resultado)

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoy", hoy))
    app.add_handler(CommandHandler("banco", banco))
    app.run_polling()

if __name__ == "__main__":
    main()
