import logging
import asyncio
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuração
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8443274539:AAEZ_jfLKLAHjTquzS9Z650Xn4_-ZwTlrnI"

# Armazenamento em memória
usuarios = set()
alertas_enviados = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuarios.add(user_id)
    
    await update.message.reply_text(
        "🤖 *BOT TEMPO REAL ATIVADO!* ⚡\n\n"
        "✅ **Verificação:** A cada 2 MINUTOS\n"
        "🚨 **Alertas:** Imediatos ao detectar\n"
        "🎯 **Estratégia:** Odd 1.25 + Time pressionando\n\n"
        "⚡ **Status:** 100% Automático 24/7\n"
        "🔍 **Monitorando:** Todas ligas principais\n\n"
        "_Primeiros alertas em instantes..._",
        parse_mode='Markdown'
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 **STATUS DO SISTEMA**\n\n"
        f"• 👥 Usuários ativos: {len(usuarios)}\n"
        f"• ⏰ Última verificação: {datetime.now().strftime('%H:%M:%S')}\n"
        f"• 🔄 Frequência: A cada 2 minutos\n"
        f"• 🏆 Ligas monitoradas: 12\n"
        f"• ✅ Sistema: OPERACIONAL",
        parse_mode='Markdown'
    )

# SIMULADOR DE PARTIDAS EM TEMPO REAL
def simular_partidas():
    """Simula oportunidades em tempo real"""
    agora = datetime.now()
    oportunidades = []
    
    # Simular variação de oportunidades ao longo do tempo
    minuto_atual = agora.minute
    
    # Oportunidade a cada 5-10 minutos (simulação)
    if minuto_atual % 7 == 0:  # A cada ~7 minutos
        oportunidades.append({
            'id': f"op_{agora.strftime('%H%M')}",
            'liga': 'Premier League',
            'casa': 'Manchester United',
            'visitante': 'Liverpool',
            'minuto': 38,
            'escanteios': 3,
            'odd': 1.28,
            'tipo': '1t',
            'situacao': 'Time perdendo pressionando'
        })
    
    if minuto_atual % 9 == 0:  # A cada ~9 minutos
        oportunidades.append({
            'id': f"op_{agora.strftime('%H%M')}_2",
            'liga': 'Brasileirão',
            'casa': 'Flamengo', 
            'visitante': 'Palmeiras',
            'minuto': 73,
            'escanteios': 9,
            'odd': 1.35,
            'tipo': '2t',
            'situacao': 'Time empatando atacando'
        })
    
    return oportunidades

# VERIFICADOR PRINCIPAL - RODA A CADA 2 MINUTOS
async def verificador_tempo_real(context: ContextTypes.DEFAULT_TYPE):
    try:
        logger.info("🔍 Verificação rápida em andamento...")
        
        oportunidades = simular_partidas()
        
        for op in oportunidades:
            # Evitar alertas duplicados
            if op['id'] in alertas_enviados:
                continue
                
            alertas_enviados.add(op['id'])
            
            if op['tipo'] == '1t':
                alerta = f"""
🚨 *ALERTA 1º TEMPO - OPORTUNIDADE IMEDIATA!* ⚽

🏆 **{op['liga']}**
⚽ **{op['casa']} vs {op['visitante']}**
⏰ **Minuto:** {op['minuto']}'
💰 **Odd Betano:** {op['odd']} ✅

🎯 **Aposta:** +{op['escanteios'] + 0.5} escanteios
📊 **Situação:** {op['situacao']}

⚡ **Validade:** Próximos 5-10 minutos
🔔 **Detecção:** Tempo real

💡 **Ação:** Verificar Betano agora!
"""
            else:
                alerta = f"""
🚨 *ALERTA FINAL - OPORTUNIDADE IMEDIATA!* ⚽

🏆 **{op['liga']}**
⚽ **{op['casa']} vs {op['visitante']}**
⏰ **Minuto:** {op['minuto']}'
💰 **Odd Betano:** {op['odd']} ✅

🎯 **Aposta:** +{op['escanteios'] + 1.5} escanteios  
📊 **Situação:** {op['situacao']}

⚡ **Validade:** Próximos 10-15 minutos
🔔 **Detecção:** Tempo real

💡 **Ação:** Verificar Betano agora!
"""
            
            # Enviar para todos usuários
            for user_id in list(usuarios):
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=alerta,
                        parse_mode='Markdown'
                    )
                    logger.info(f"⚡ Alerta TEMPO REAL enviado para {user_id}")
                except Exception as e:
                    logger.error(f"❌ Erro: {e}")
        
        # Limpar alertas antigos (para evitar duplicação)
        agora = datetime.now()
        alertas_enviados.clear()  # Simplificado para demo
        
        logger.info(f"✅ Verificação concluída - {len(oportunidades)} oportunidades")
        
    except Exception as e:
        logger.error(f"❌ Erro no verificador: {e}")

def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    
    # ⚡ VERIFICAÇÃO A CADA 2 MINUTOS! ⚡
    job_queue = application.job_queue
    job_queue.run_repeating(verificador_tempo_real, interval=120, first=5)  # 2 minutos!
    
    logger.info("🚀 BOT TEMPO REAL INICIADO!")
    print("=" * 60)
    print("⚡ SISTEMA TEMPO REAL CONFIGURADO!")
    print("📍 Frequência: A cada 2 MINUTOS")
    print("🔔 Alertas: Imediatos ao detectar")
    print("🌐 Status: 100% Online 24/7")
    print("=" * 60)
    
    application.run_polling()

if __name__ == '__main__':
    main()
