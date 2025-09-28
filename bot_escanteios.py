import logging
import requests
from flask import Flask, request, abort
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ————————————— Configurações iniciais —————————————

# Token fixo no código (não recomendado para produção)
TOKEN = "8443274539:AAE-OZWtG_oqwOF3UEKNIS-UvcNsL1EC2ys"

# Porta padrão (usada pelo Render)
PORT = 8000

# Hostname definido pelo Render (você pode trocar pelo seu domínio público, se tiver)
HOSTNAME = "SEU_HOST.render.com"  # <-- troque aqui pelo seu domínio Render

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{HOSTNAME}{WEBHOOK_PATH}"

# Logging
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cria a aplicação do Telegram
application = Application.builder().token(TOKEN).build()

# ————————————— Comandos do bot —————————————

usuarios = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios:
        usuarios.append(user_id)
    await update.message.reply_text("🤖 Bot ativo via Webhook!")

application.add_handler(CommandHandler("start", start))

# ————————————— Webhook endpoint —————————————

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        application.update_queue.put(update)
        return "OK"
    else:
        abort(400)

# ————————————— Função para configurar o webhook no Telegram —————————————

def set_webhook():
    logger.info(f"Definindo webhook: {WEBHOOK_URL}")
    url = f"https://api.telegram.org/bot{TOKEN}/setWebhook?url={WEBHOOK_URL}"
    resp = requests.get(url)
    if resp.status_code == 200:
        logger.info("✅ Webhook definido com sucesso!")
    else:
        logger.error(f"❌ Falha ao definir webhook: {resp.status_code} — {resp.text}")

# ————————————— Execução principal —————————————

if __name__ == "__main__":
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
