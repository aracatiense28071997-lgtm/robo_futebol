import http.server
import json
import socketserver
import threading
import time
from datetime import datetime
import requests

# 🔑 CONFIGURAÇÕES VALIDADAS DO SEU BOT TELEGRAM
CHAT_ID = 1027409830
TELEGRAM_TOKEN = "8200577138:AAFdKrmOv2QQKrvfLGujQPe4yhiME-w4GzU"

URL_SEND = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
URL_UPDATES = f"https://telegram.org{TELEGRAM_TOKEN}/getUpdates"

alertas_enviados = []
jogos_manuais = []
ultimo_update_id = 0

def enviar_alerta_telegram(mensagem):
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(URL_SEND, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# ==============================================================================
# 🗣️ MOTOR: ESCUTA DE COMANDOS INTERATIVOS DO TELEGRAM
# ==============================================================================
def processar_comandos_telegram():
    global ultimo_update_id
    try:
        url = f"{URL_UPDATES}?offset={ultimo_update_id + 1}&timeout=10"
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return
            
        dados = response.json()
        for update in dados.get("result", []):
            ultimo_update_id = update["update_id"]
            message = update.get("message", {})
            texto_comando = message.get("text", "").strip()
            chat_remetente = message.get("chat", {}).get("id")

            if chat_remetente != CHAT_ID:
                continue

            if texto_comando.startswith("/jogo"):
                conteudo_jogo = texto_comando.replace("/jogo", "").strip()
                if not conteudo_jogo:
                    enviar_alerta_telegram("⚠️ *Erro de digitação!*\nUse o formato correto:\n`/jogo Flamengo vs Vasco - 16h00`")
                else:
                    jogos_manuais.append(conteudo_jogo)
                    enviar_alerta_telegram(f"✅ *Jogo Cadastrado com Sucesso!*\n📌 Mapeado para análise pré-jogo:\n`{conteudo_jogo}`")

            elif texto_comando == "/aovivo":
                enviar_alerta_telegram("📡 *Iniciando varredura global nos canais esportivos...*")
                
                esportes_links = {
                    "⚽ FUTEBOL": "soccer",
                    "🏒 HÓQUEI": "hockey",
                    "🏀 BASQUETE": "basketball",
                    "🎾 TÊNIS": "tennis",
                    "🏈 NFL": "americanfootball"
                }
                
                msg_live = "📟 *PAINEL DE JOGOS AO VIVO AGORA:* 📟\n\n"
                encontrou_jogos = False
                
                for nome_esp, id_esp in esportes_links.items():
                    try:
                        url_live = f"https://spoyer.com{id_esp}"
                        res = requests.get(url_live, timeout=8).json()
                        jogos_live = res.get("games", [])
                        
                        if jogos_live:
                            msg_live += f"🔹 *{nome_esp}* 🔹\n"
                            for j in jogos_live[:2]:
                                msg_live += f"⚔️ {j.get('home', {}).get('name')} {j.get('score', '0:0')} {j.get('away', {}).get('name')} ({j.get('time', 'Live')})\n"
                            msg_live += "-------------------------------------\n"
                            encontrou_jogos = True
                    except Exception:
                        pass
                
                if encontrou_jogos:
                    enviar_alerta_telegram(msg_live)
                else:
                    enviar_alerta_telegram("📭 Nenhum evento esportivo ativo no mundo passando pelos canais neste minuto.")

            elif texto_comando == "/lista":
                if not jogos_manuais:
                    enviar_alerta_telegram("📭 Sua lista de pré-jogo manual está vazia no momento.")
                else:
                    msg_lista = "📋 *SUA GRADE PRÉ-JOGO CADASTRADA:* 📋\n\n"
                    for idx, j in enumerate(jogos_manuais, 1):
                        msg_lista += f"{idx}. `{j}`\n"
                    enviar_alerta_telegram(msg_lista)

    except Exception as e:
        print(f"Erro na escuta do Telegram: {e}")

# ==============================================================================
# 🎯 MONITORAMENTO INTELIGENTE EM LOOP AO VIVO (5 ESPORTES)
# ==============================================================================
def executar_analise_esportiva_live():
    esportes = {
        "FUTEBOL": "https://spoyer.comsoccer",
        "HOQUEI NO GELO": "https://spoyer.comhockey",
        "BASQUETE": "https://spoyer.combasketball",
        "TENIS": "https://spoyer.comtennis",
        "FUTEBOL AMERICANO": "https://spoyer.comamericanfootball"
    }

    for esporte, url in esportes.items():
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                continue

            dados = response.json()
            jogos = dados.get("games", [])

            for jogo in jogos:
                id_jogo = jogo.get("game_id")
                if id_jogo in alertas_enviados:
                    continue

                time_casa = jogo.get("home", {}).get("name", "Equipe Casa")
                time_fora = jogo.get("away", {}).get("name", "Equipe Fora")
                liga = jogo.get("league", {}).get("name", "Torneio")
                placar = jogo.get("score", "0:0")
                tempo = jogo.get("time", "Ao vivo")

                disparar = False
                call_estrategia = ""
                
                minuto_atual = 0
                if tempo and "'" in tempo:
                    try:
                        minuto_atual = int(tempo.replace("'", ""))
                    except:
                        pass

                # ⚽ FUTEBOL
                if esporte == "FUTEBOL":
                    gols = placar.split(":")
                    if len(gols) == 2:
                        g_casa = int(gols[0])
                        g_fora = int(gols[1])
                        chutes_totais = int(jogo.get("shots_home", 0)) + int(jogo.get("shots_away", 0))

                        if 15 <= minuto_atual <= 35 and g_casa == g_fora and chutes_totais >= 6:
                            disparar = True
                            call_estrategia = f"🔥 *ESTRATÉGIA: GOL NO PRIMEIRO TEMPO (HT)* 🔥\n🎯 *Sugestão:* Over 0.5 Gols HT.\n📊 Pressão forte: {chutes_totais} finalizações."
                        elif minuto_atual >= 70 and chutes_totais >= 12 and (g_casa == g_fora or abs(g_casa - g_fora) == 1):
                            disparar = True
                            call_estrategia = f"🔥 *ESTRATÉGIA: GOL NO SEGUNDO TEMPO (FT)* 🔥\n🎯 *Sugestão:* Over Gols Limite FT.\n📊 Ritmo crítico com {chutes_totais} chutes no total!"

                # 🏒 HÓQUEI NO GELO
                elif esporte == "HOQUEI NO GELO":
                    chutes_SOG = int(jogo.get("shots_home", 0)) + int(jogo.get("shots_away", 0))
                    if chutes_SOG >= 18:
                        disparar = True
                        call_estrategia = f"🏒 *ESTRATÉGIA: OVER GOLS HÓQUEI AO VIVO* 🏒\n🎯 *Sugestão:* Over Gols no Período Atual.\n📊 Bombardeio na pista! {chutes_SOG} finalizações registradas."

                # 🏀 BASQUETE
                elif esporte == "BASQUETE" and ("4th" in tempo or "Quarter 4" in tempo):
                    pontos = placar.split("-")
                    if len(pontos) == 2:
                        p_casa = int(pontos[0])
                        p_fora = int(pontos[1])
                        if abs(p_casa - p_fora) <= 3:
                            disparar = True
                            call_estrategia = f"🏀 *ESTRATÉGIA: BASQUETE LIVE* 🏀\n🎯 *Sugestão:* OVER pontos no Quarto Final.\n📊 Cronômetro parando muito por faltas táticas."

                # 🎾 TÊNIS
                elif esporte == "TENIS":
                    if "5:5" in placar or "6:5" in placar or "5:6" in placar:
                        disparar = True
                        call_estrategia = f"🎾 *ESTRATÉGIA: TÊNIS LIVE* 🎾\n🎯 *Sugestão:* Vencedor do Próximo Game (Sacador).\n📊 Reta final equilibrada de set com vantagem para quem saca."

                # 🏈 FUTEBOL AMERICANO (NFL)
                elif esporte == "FUTEBOL AMERICANO" and ("4th" in tempo or "Quarter 4" in tempo):
                    pontos_nfl = placar.split("-")
                    if len(pontos_nfl) == 2:
                        p_casa_nfl = int(pontos_nfl[0])
                        p_fora_nfl = int(pontos_nfl[1])
                        diff_nfl = abs(p_casa_nfl - p_fora_nfl)
                        if diff_nfl <= 7:
                            disparar = True
                            call_estrategia = f"🏈 *ESTRATÉGIA: NFL LIVE (FINAL DE JOGO)* 🏈\n🎯 *Sugestão:* Handicap de Pontos ou Over Pontos Limite.\n📊 Reta final dramática de pré-temporada!"

                if disparar:
                    msg = f"🚨 *ROBÔ ARACATIENSE: ALERTA EM TEMPO REAL* 🚨\n\n📊 *Modalidade:* {esporte}\n🏆 *Liga:* {liga}\n⚔️ *Confronto:* {time_casa} vs {time_fora}\n📈 *Placar:* {placar} ({tempo})\n\n{call_estrategia}"
                    enviar_alerta_telegram(msg)
                    alertas_enviados.append(id_jogo)

        except Exception as e:
            print(f"Aviso na modalidade {esporte}: {e}")

# Loops paralelos do sistema na Nuvem
def loop_da_escuta_comandos():
    while True:
        processar_comandos_telegram()
        time.sleep(1)

def loop_do_monitor_live():
