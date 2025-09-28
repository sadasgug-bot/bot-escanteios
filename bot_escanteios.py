import os
import logging
import asyncio
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8443274539:AAEZ_jfLKLAHjTquzS9Z650Xn4_-ZwTlrnI"
API_FOOTBALL_KEY = "a41e060f1db0909fd4ff8d7fed3bc37e"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

usuarios = []

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in usuarios:
        usuarios.append(user_id)
    
    await update.message.reply_text(
        "🤖 *BOT DE ESCANTEIOS - ONLINE!* ✅\n\n"
        "Sistema conectado à API-Football para alertas ao vivo de todas as partidas.\n"
        "Digite /teste para ver exemplo.\n"
        "Digite /estrategia para detalhes da estratégia.",
        parse_mode='Markdown'
    )
    logger.info(f"Usuário {user_id} iniciou o bot")

async def teste(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔔 *ALERTA TESTE - SISTEMA OPERACIONAL* ⚽\n"
        "Bot respondendo corretamente.",
        parse_mode='Markdown'
    )

async def estrategia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎯 Estratégia:\n"
        "- Alertas no 1º tempo (0-30min): +5 escanteios + xG > 0.50 + time favorito perdendo/empatando\n"
        "- Alertas no final (70+min): xG > 1.50 + time favorito pressionando\n"
        "Aposta: +0.5 escanteios\n",
        parse_mode='Markdown'
    )

def get_live_fixtures():
    """Busca partidas ao vivo via API-Football"""
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    params = {
        "live": "all"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        return data['response']
    except Exception as e:
        logger.error(f"Erro ao buscar partidas ao vivo: {e}")
        return []

def analisar_partida_api(partida):
    """Analisa uma partida da API-Football para alertas"""

    fixture = partida['fixture']
    teams = partida['teams']
    goals = partida['goals']
    statistics = partida.get('statistics', [])

    minuto = fixture['status']['elapsed']
    if minuto is None:
        minuto = 0

    tipo = '1t' if minuto <= 45 else '2t'

    escanteios_casa = None
    xg_casa = None

    for stat in statistics:
        if stat['team']['id'] == teams['home']['id']:
            for s in stat['statistics']:
                if s['type'] == 'Corner Kicks':
                    escanteios_casa = s['value']
                if s['type'] == 'Expected Goals':
                    xg_casa = s['value']
            break

    if escanteios_casa is None or xg_casa is None:
        return False, []

    placar_casa = goals['home']
    placar_visitante = goals['away']
    favorito_perdendo_empatando = placar_casa <= placar_visitante

    condicoes = []

    if tipo == '1t' and minuto <= 30:
        if escanteios_casa >= 5:
            condicoes.append(f"✅ +5 escanteios (Casa: {escanteios_casa})")
        if xg_casa > 0.50 and favorito_perdendo_empatando:
            condicoes.append(f"✅ xG casa > 0.50 ({xg_casa}) e perdendo/empatando")
        return len(condicoes) >= 1, condicoes

    if tipo == '2t' and minuto >= 70:
        if xg_casa > 1.50 and favorito_perdendo_empatando:
            condicoes.append(f"✅ xG casa > 1.50 ({xg_casa}) e perdendo/empatando")
        return len(condicoes) >= 1, condicoes

    return False, []

async def alertas_estrategia_xg(context: ContextTypes.DEFAULT_TYPE):
    if not usuarios:
        return

    partidas_ao_vivo = get_live_fixtures()

    if not partidas_ao_vivo:
        logger.info("Nenhuma partida ao vivo no momento.")
        return

    for partida in partidas_ao_vivo:
        oportunidade, condicoes = analisar_partida_api(partida)

        if oportunidade:
            fixture = partida['fixture']
            goals = partida['goals']
            teams = partida['teams']

            alerta = (
                f"🚨 *ALERTA PARTIDA AO VIVO* ⚽\n"
                f"🏆 {fixture['league']['name']} - {fixture['round']}\n"
                f"⚽ {teams['home']['name']} {goals['home']} x {goals['away']} {teams['away']['name']}\n"
                f"⏰ Minuto: {fixture['status']['elapsed']}'\n"
                f"✅ CONDIÇÕES ATENDIDAS:\n" + "\n".join(condicoes) + "\n"
                f"⚡ OPORTUNIDADE: +0.5 escanteios\n"
            )

            for user_id in usuarios:
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=alerta,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Alerta enviado para usuário {user_id}")
                except Exception as e:
                    logger.error(f"Erro ao enviar alerta para {user_id}: {e}")

def main():
    try:
        application = Application.builder().token(TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("teste", teste))
        application.add_handler(CommandHandler("estrategia", estrategia))

        job_queue = application.job_queue
        job_queue.run_repeating(alertas_estrategia_xg, interval=420, first=10)

        logger.info("Bot iniciado.")
        application.run_polling()

    except Exception as e:
        logger.error(f"Erro ao iniciar bot: {e}")

if __name__ == "__main__":
    main()
