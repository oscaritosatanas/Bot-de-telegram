from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import logging
import random

# Configurar el logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Token del bot
TOKEN = '7669037266:AAEmK4wxtlGhWwgbcWc2wJpHj-b_QHP64GE'

# Dirección de la wallet
wallet_address = "0x743cc8a13f179950025ee65b9c13addc6f4e4546"

# ID del administrador en Telegram
ADMIN_TELEGRAM_ID = 1406608997  # Asegúrate de que este es tu ID real

# Diccionario para almacenar ventas en espera de aprobación
ventas_pendientes = {}

# Función de inicio
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔹 Para continuar, ingresa tu número de móvil:")
    return

# Manejar datos del usuario
async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    message_text = update.message.text.strip()

    if user_id not in ventas_pendientes:
        ventas_pendientes[user_id] = {}

    venta = ventas_pendientes[user_id]

    if "móvil" not in venta:
        venta["móvil"] = message_text
        await update.message.reply_text("🔹 Ahora ingresa el número de tu tarjeta:")
        return

    elif "tarjeta" not in venta:
        venta["tarjeta"] = message_text
        await update.message.reply_text("🔹 Ingresa la cantidad de MTT que deseas vender:")
        return

    elif "cantidad_MTT" not in venta:
        if message_text.isdigit():
            cantidad = int(message_text)
            venta["cantidad_MTT"] = cantidad
            venta["codigo_venta"] = random.randint(1000, 9999)  # Genera un código único de 4 dígitos
            await update.message.reply_text("📸 Envía la captura de pantalla de la transferencia para confirmar el pago.")
        else:
            await update.message.reply_text("⚠️ Ingresa una cantidad válida de MTT.")
        return

# Manejar imagen del usuario
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id

    if user_id not in ventas_pendientes or "cantidad_MTT" not in ventas_pendientes[user_id]:
        await update.message.reply_text("⚠️ No se ha solicitado una imagen en este momento.")
        return

    # Obtener la foto y los datos
    venta = ventas_pendientes[user_id]
    photo = update.message.photo[-1].file_id

    # Enviar la imagen y datos al administrador
    mensaje_admin = (
        f"📝 **Nueva Venta de MTT**\n\n"
        f"👤 Usuario: {user.first_name}\n"
        f"📱 Móvil: {venta['móvil']}\n"
        f"💳 Tarjeta: {venta['tarjeta']}\n"
        f"💰 Cantidad: {venta['cantidad_MTT']} MTT\n"
        f"🔢 Número de venta: {venta['codigo_venta']}\n"
        "📸 Imagen adjunta.\n\n"
        "⚠️ Para aceptar la transacción, escribe: **/ok {venta['codigo_venta']}**"
    )

    await context.bot.send_photo(chat_id=ADMIN_TELEGRAM_ID, photo=photo, caption=mensaje_admin)
    await update.message.reply_text("✅ Imagen enviada. Espera la confirmación del administrador.")

# Comando para que el administrador apruebe la venta
async def approve_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_TELEGRAM_ID:
        await update.message.reply_text("⚠️ No tienes permisos para usar este comando.")
        return

    try:
        codigo_venta = int(context.args[0])  # Obtener el número de venta

        # Buscar la venta por código
        for user_id, venta in ventas_pendientes.items():
            if venta.get("codigo_venta") == codigo_venta:
                await context.bot.send_message(chat_id=user_id, text="✅ Tu venta ha sido aceptada. En breve recibirás tu pago.")
                await update.message.reply_text(f"✅ Transacción aprobada para la venta {codigo_venta}.")
                del ventas_pendientes[user_id]  # Eliminar la venta tras la aprobación
                return
        
        await update.message.reply_text("⚠️ No se encontró ninguna venta con ese número.")
    
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ Debes proporcionar un número de venta válido. Usa: `/ok <número_de_venta>`")

# Crear y ejecutar la aplicación
def run_bot():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ok", approve_transaction))  # Aprobación de la venta
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    application.run_polling()

if __name__ == "__main__":
    run_bot()
