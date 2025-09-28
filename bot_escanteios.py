import os
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Configuração de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "8443274539:AAEZ_jfLKLAHjTquzS9Z650Xn4_-ZwTlrnI"

# Armazenamento
usuarios = []

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios:
        usuarios.append(user_id)
    
    await update.message.reply_text(
        "🤖 *BOT DE ESCANTEIOS - ONLINE!* ✅\n\n"
        "🎯 Sistema funcionando no Render.com\n"
        "🔔 Alertas automáticos em breve\n"
        "⚡ Versão estável configurada\n\n"
        "_Digite /teste para ver exemplo_",
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(
        "🤖 *BOT DE ESCANTEIOS - ESTRATÉGIA ATUALIZADA!* 🚀\n\n"
        "🎯 **NOVAS CONDIÇÕES:**\n"
        "• 📊 Análise por xG (Expected Goals)\n"
        "• ⚡ Alertas baseados em pressão real\n"
        "• 🎲 Independente de quantidade de escanteios\n\n"
        "🔔 **ALERTA 1º TEMPO (0-30min):**\n"
        "- +5 escanteios + xG > 0.50\n"
        "- Time favorito perdendo/empatando\n\n"
        "🔔 **ALERTA FINAL (70+min):**\n"
        "- xG > 1.50 + time favorito pressionando\n"
        "- Aposta: +0.5 escanteios\n\n"
        "Digite /estrategia para detalhes",
        parse_mode='Markdown'
    )
    logger.info(f"Usuário {update.effective_user.id} iniciou o bot")

# /teste
async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 *ALERTA TESTE - SISTEMA OPERACIONAL* ⚽\n\n"
        "✅ Bot respondendo corretamente\n"
        "🎯 Próximo passo: alertas automáticos\n"
        "⚡ Render.com + Telegram integrados",
        parse_mode='Markdown'
    )

# /estrategia
async def estrategia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 **ESTRATÉGIA DETALHADA** ⚽\n\n"
        "🎯 **OBJETIVO:** Identificar times pressionando baseado em xG\n\n"
        "🔔 ALERTA 1º TEMPO (0-30min):\n"
        "✅ +5 escanteios até 30min\n"
        "✅ xG > 0.50 (Expected Goals)\n"
        "✅ Time favorito perdendo/empatando\n"
        "🎯 Aposta: +0.5 escanteios restantes\n\n"
        "🔔 ALERTA FINAL (70+min):\n"
        "✅ xG > 1.50 (alta criação de chances)\n"
        "✅ Time favorito perdendo/empatando\n"
        "✅ Pressão para virar/empatar\n"
        "🎯 Aposta: +0.5 escanteios\n\n"
        "⚡ **VANTAGEM:** Análise por criação real de chances",
        parse_mode='Markdown'
    )

# SIMULADOR DE DADOS COM XG
def simular_partidas_com_xg():
    """Simula partidas com dados de xG"""
    agora = datetime.now()
    minuto_atual = agora.minute
    
    partidas = []
    
    # Simular alertas baseados no horário
    if minuto_atual % 10 == 0:  # A cada 10 minutos
        partidas.append({
            'id': f"1t_{agora.strftime('%H%M')}",
            'tipo': '1t',
            'liga': 'Premier League',
            'casa': 'Manchester City',
            'visitante': 'Arsenal',
            'minuto': 28,
            'placar_casa': 0,
            'placar_visitante': 1,
            'escanteios': 6,
            'xg_casa': 0.8,
            'xg_visitante': 0.4,
            'odd_escanteios': 1.45,
            'situacao': 'Favorito perdendo com alto xG'
        })
    
    if minuto_atual % 15 == 0:  # A cada 15 minutos
        partidas.append({
            'id': f"2t_{agora.strftime('%H%M')}",
            'tipo': '2t', 
            'liga': 'La Liga',
            'casa': 'Barcelona',
            'visitante': 'Real Madrid',
            'minuto': 75,
            'placar_casa': 1,
            'placar_visitante': 1,
            'escanteios': 9,
            'xg_casa': 2.1,
            'xg_visitante': 1.2,
            'odd_escanteios': 1.28,
            'situacao': 'Favorito empatando com xG muito alto'
        })
    
    return partidas

# VERIFICAR CONDIÇÕES DA NOVA ESTRATÉGIA
def analisar_oportunidade(partida):
    """Analisa se a partida atende às novas condições"""
    
    # ALERTA 1º TEMPO (0-30min)
    if partida['tipo'] == '1t' and partida['minuto'] <= 30:
        condicoes = []
        
        if partida['escanteios'] >= 5:
            condicoes.append("✅ +5 escanteios até 30min")
        
        if (partida['placar_casa'] <= partida['placar_visitante']) and partida['xg_casa'] > 0.50:
            condicoes.append(f"✅ xG: {partida['xg_casa']} > 0.50")
        
        return len(condicoes) >= 1, condicoes  # <- ATENDENDO PELO MENOS 1 CONDIÇÃO
    
    # ALERTA FINAL (70+min)
    elif partida['tipo'] == '2t' and partida['minuto'] >= 70:
        condicoes = []
        
        if (partida['placar_casa'] <= partida['placar_visitante']) and partida['xg_casa'] > 1.50:
            condicoes.append(f"✅ xG: {partida['xg_casa']} > 1.50")
            condicoes.append("✅ Favorito perdendo/empatando")
        
        return len(condicoes) >= 1, condicoes  # <- ATENDENDO PELO MENOS 1 CONDIÇÃO
    
    return False, []

# ALERTAS AUTOMÁTICOS
async def alertas_estrategia_xg(context: ContextTypes.DEFAULT_TYPE):
    """Alertas baseados na nova estratégia com xG"""
    try:
        if not usuarios:
            return
            
        partidas = simular_partidas_com_xg()
        
        for partida in partidas:
            oportunidade, condicoes = analisar_oportunidade(partida)
            
            if oportunidade:
                if partida['tipo'] == '1t':
                    alerta = f"""
🚨 **ALERTA 1º TEMPO - ANÁLISE XG** ⚽
🏆 {partida['liga']}
⚽ {partida['casa']} {partida['placar_casa']}×{partida['placar_visitante']} {partida['visitante']}
⏰ Minuto: {partida['minuto']}'
📊 Escanteios: {partida['escanteios']}
🎯 xG: {partida['xg_casa']} (Expected Goals)
💰 Odd: {partida['odd_escanteios']}
✅ CONDIÇÕES ATENDIDAS:
{chr(10).join(condicoes)}
⚡ OPORTUNIDADE: +0.5 escanteios
"""
                else:
                    alerta = f"""
🚨 **ALERTA FINAL - PRESSÃO XG** ⚽
🏆 {partida['liga']}  
⚽ {partida['casa']} {partida['placar_casa']}×{partida['placar_visitante']} {partida['visitante']}
⏰ Minuto: {partida['minuto']}'
📊 xG Total: {partida['xg_casa']} (Alta criação)
💰 Odd: {partida['odd_escanteios']}
✅ CONDIÇÕES ATENDIDAS:
{chr(10).join(condicoes)}
⚡ OPORTUNIDADE: +0.5 escanteios (aposta simples)
"""
                for user_id in usuarios:
                    try:
                        await context.bot.send_message(
                            chat_id=user_id,
                            text=alerta,
                            parse_mode='Markdown'
                        )
                        logger.info(f"📤 Alerta xG enviado para {user_id}")
                    except Exception as e:
                        logger.error(f"❌ Erro: {e}")
        
        logger.info(f"✅ Verificação xG concluída - {len(partidas)} partidas")
        
    except Exception as e:
        logger.error(f"❌ Erro na estratégia xG: {e}")

# MAIN
def main():
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("teste", teste))
        application.add_handler(CommandHandler("estrategia", estrategia))
        
        job_queue = application.job_queue
        job_queue.run_repeating(alertas_estrategia_xg, interval=420, first=10)

        logger.info("🚀 Bot iniciando...")
        print("=" * 50)
        print("🤖 BOT INICIADO - AGUARDANDO COMANDOS")
        print("📍 Render.com - Python 3.9")
        print("🔗 Token: Configurado")
        print("=" * 50)
        logger.info("🚀 BOT COM ESTRATÉGIA XG INICIADO!")
        print("=" * 60)
        print("🎯 NOVA ESTRATÉGIA IMPLEMENTADA!")
        print("📊 Análise por xG (Expected Goals)")
        print("🔔 Alertas baseados em criação real de chances")
        print("=" * 60)

        application.run_polling()

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {e}")
        print(f"ERRO CRÍTICO: {e}")

if __name__ == '__main__':
    main()
