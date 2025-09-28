import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuração
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8443274539:AAEZ_jfLKLAHjTquzS9Z650Xn4_-ZwTlrnI"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *BOT DE ESCANTEIOS - ONLINE!* ✅\n\n"
        "🎯 Sistema funcionando no Render.com\n"
        "🔔 Alertas automáticos em breve\n"
        "⚡ Versão estável configurada\n\n"
        "_Digite /teste para ver exemplo_",
        parse_mode='Markdown'
    )
    logger.info(f"Usuário {update.effective_user.id} iniciou o bot")

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 *ALERTA TESTE - SISTEMA OPERACIONAL* ⚽\n\n"
        "✅ Bot respondendo corretamente\n"
        "🎯 Próximo passo: alertas automáticos\n"
        "⚡ Render.com + Telegram integrados",
        parse_mode='Markdown'
    )

def main():
    try:
        # Criar aplicação
        application = Application.builder().token(TOKEN).build()
        
        # Adicionar comandos
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("teste", teste))
        
        logger.info("🚀 Bot iniciando...")
        print("=" * 50)
        print("🤖 BOT INICIADO - AGUARDANDO COMANDOS")
        print("📍 Render.com - Python 3.9")
        print("🔗 Token: Configurado")
        print("=" * 50)
        
        # Iniciar bot
        application.run_polling()
        
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {e}")
        print(f"ERRO CRÍTICO: {e}")

if __name__ == '__main__':
    main()
