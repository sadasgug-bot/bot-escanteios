import os
import logging
import requests
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configurações
TOKEN = os.getenv("TOKEN")  # Configure no Render a variável TOKEN
PORT = int(os.getenv("PORT", "8000"))
WEBHOOK_PATH = "/webhook"  # Caminho que o Telegram vai chamar
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# Logger
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Inicializa o Application do telegram
application = Application.builder().token(TOKEN).build()

usuarios = []

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios:
        usuarios.append(user_id)
    await update.message.reply_text("🤖 Bot ativo via Webhook no Render!")

application.add_handler(CommandHandler("start", start))


# Endpoint do webhook
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
        return "OK"
    else:
        abort(400)


def set_webhook():
    logger.info(f"Setando webhook: {WEBHOOK_URL}")
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    resp = requests.get(url)
    if resp.status_code == 200:
        logger.info("Webhook setado com sucesso!")
    else:
        logger.error(f"Erro ao setar webhook: {resp.text}")


if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
