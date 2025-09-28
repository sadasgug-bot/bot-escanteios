import os
import logging
import requests
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ————————————— Configurações iniciais —————————————

# Pega token do ambiente
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("🔴 BOT_TOKEN não definido — configure nas variáveis de ambiente")

# Porta padrão (Render costuma define via variável PORT)
PORT = int(os.getenv("PORT", "8000"))

WEBHOOK_PATH = "/webhook"  # caminho do endpoint
# Construir URL completa do webhook (Render disponibiliza hostname via variável)
HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if not HOSTNAME:
    raise ValueError("🔴 RENDER_EXTERNAL_HOSTNAME não definido — essencial para webhook URL")

WEBHOOK_URL = f"https://{HOSTNAME}{WEBHOOK_PATH}"

# Logging
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cria aplicação Telegram
application = Application.builder().token(TOKEN).build()

# ————————————— Comandos do bot —————————————

usuarios = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios:
        usuarios.append(user_id)
    await update.message.reply_text("🤖 Bot ativo via Webhook!")

application.add_handler(CommandHandler("start", start))

# Você pode adicionar outros comandos como /estrategia, etc

# ————————————— Webhook endpoint —————————————

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
        return "OK"
    else:
        abort(400)

# ————————————— Função para setar webhook no Telegram —————————————

def set_webhook():
    logger.info(f"Definindo webhook: {WEBHOOK_URL}")
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    resp = requests.get(url)
    if resp.status_code == 200:
        logger.info("Webhook definido com sucesso!")
    else:
        logger.error(f"Falha ao definir webhook: {resp.status_code} — {resp.text}")

# ————————————— Execução principal —————————————

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
