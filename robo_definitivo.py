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
jogos_manuais = []  # Lista na memória para guardar os jogos que você cadastrar
ultimo_update_id = 0

def enviar_alerta_telegram(mensagem):
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(URL_SEND, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# ==============================================================================
# 🗣️ NOVO MOTOR: ESCUTA DE COMANDOS INTERATIVOS DO TELEGRAM
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

            # Garante que o robô só obedece as ordens vindas do seu CHAT_ID
            if chat_remetente != CHAT_ID:
                continue

            # 🛠️ COMANDO 1: CADASTRO MANUAL DE JOGOS DO DIA
            if texto_comando.startswith("/jogo"):
                conteudo_jogo = texto_comando.replace("/jogo", "").strip()
                if not conteudo_jogo:
                    enviar_alerta_telegram("⚠️ *Erro de digitação!*\nUse o formato correto:\n`/jogo Flamengo vs Vasco - 16h00`")
                else:
                    jogos_manuais.append(conteudo_jogo)
                    enviar_alerta_telegram(f"✅ *Jogo Cadastrado com Sucesso!*\n📌 Mapeado para análise pré-jogo:\n`{conteudo_jogo}`")

            # 📊 COMANDO 2: CONSULTAR PLACAR E JOGOS ATIVOS NO AO VIVO AGORA
            elif texto_comando == "/aovivo":
                enviar_alerta_telegram("📡 *Consultando canais ao vivo de futebol...*")
                
                url_soccer = "https://spoyer.com"
                try:
                    res = requests.get(url_soccer, timeout=10).json()
                    jogos_live = res.get("games", [])
                    
                    if not jogos_live:
                        enviar_alerta_telegram("📭 Nenhuma partida de futebol ativa no funil de monitoramento neste minuto.")
                        continue
                        
                    msg_live = "📟 *PAINEL DE JOGOS AO VIVO AGORA:* 📟\n\n"
                    # Exibe as primeiras 4 partidas em andamento na rede
                    for j in jogos_live[:4]:
                        msg_live += (
                            f"🏆 *{j.get('league', {}).get('name', 'Torneio')}*\n"
                            f"⚔️ {j.get('home', {}).get('name')} {j.get('score', '0:0')} {j.get('away', {}).get('name')}\n"
                            f"⏱️ Tempo: {j.get('time', 'Ao vivo')}\n"
                            f"-------------------------------------\n"
                        )
                    enviar_alerta_telegram(msg_live)
                except Exception:
                    enviar_alerta_telegram("⚠️ Erro temporário de conexão com os placares da rodada.")

            # 📋 COMANDO 3: CONSULTAR JOGOS CADASTRADOS MANUALMENTE
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
def monitorar_esportes_avancado():
    esportes = {
        "FUTEBOL": "https://spoyer.com",
        "HOQUEI NO GELO": "https://spoyer.com",
        "BASQUETE": "https://spoyer.com",
        "TENIS": "https://spoyer.com",
        "BEISEBOL": "https://spoyer.com"
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

                if esporte == "FUTEBOL":
                    gols = placar.split(":")
                    if len(gols) == 2:
                        g_casa, g_fora = int(gols[0]), int(gols[1])
                        chutes_totais = int(jogo.get("shots_home", 0)) + int(jogo.get("shots_away", 0))

                        if 15 <= minuto_atual <= 35 and g_casa == g_fora and chutes_totais >= 6:
                            disparar = True
                            call_estrategia = f"🔥 *ESTRATÉGIA: GOL NO PRIMEIRO TEMPO (HT)* 🔥\n🎯 *Sugestão:* Over 0.5 Gols HT.\n📊 Pressão forte: {chutes_totais} finalizações."
                        elif minuto_atual >= 70 and chutes_totais >= 12 and (g_casa == g_fora or abs(g_casa - g_fora) == 1):
                            disparar = True
                            call_estrategia = f"🔥 *ESTRATÉGIA: GOL NO SEGUNDO TEMPO (FT)* 🔥\n🎯 *Sugestão:* Over Gols Limite FT.\n📊 Ritmo crítico com {chutes_totais} chutes no total!"

                elif esporte == "HOQUEI NO GELO":
                    chutes_SOG = int(jogo.get("shots_home", 0)) + int(jogo.get("shots_away", 0))
                    if chutes_SOG >= 18:
                        disparar = True
                        call_estrategia = f"🏒 *ESTRATÉGIA: OVER GOLS HÓQUEI AO VIVO* 🏒\n🎯 *Sugestão:* Over Gols no Período Atual.\n📊 Bombardeio na pista! {chutes_SOG} finalizações registradas."

                elif esporte == "BASQUETE" and ("4th" in tempo or "Quarter 4" in tempo):
                    pontos = placar.split("-")
                    if len(pontos) == 2:
                        if abs(int(pontos[0]) - int(pontos[1])) <= 3:
                            disparar = True
                            call_estrategia = f"🏀 *ESTRATÉGIA: BASQUETE LIVE* 🏀\n🎯 *Sugestão:* OVER pontos no Quarto Final.\n📊 Cronômetro parando muito por faltas táticas."

                elif esporte == "TENIS":
                    if "5:5" in placar or "6:5" in placar or "5:6" in placar:
                        disparar = True
                        call_estrategia = f"🎾 *ESTRATÉGIA: TÊNIS LIVE* 🎾\n🎯 *Sugestão:* Vencedor do Próximo Game (Sacador).\n📊 Reta final equilibrada de set com vantagem para quem saca."

                elif esporte == "BEISEBOL" and ("8th" in tempo or "9th" in tempo):
                    corridas = placar.split("-")
                    if len(corridas) == 2 and corridas[0] == corridas[1]:
                        disparar = True
                        call_estrategia = f"⚾ *ESTRATÉGIA: INNINGS FINAIS BEISEBOL* ⚾\n🎯 *Sugestão:* Mercado de Empate na Entrada Atual."

                if disparar:
                    msg = (
                        f"🚨 *ROBÔ ARACATIENSE: ALERTA EM TEMPO REAL* 🚨\n\n"
                        f"📊 *Modalidade:* {esporte}\n"
                        f"🏆 *Liga:* {liga}\n"
                        f"⚔️ *Confronto:* {time_casa} vs {time_fora}\n"
                        f"📈 *Placar:* {placar} ({tempo})\n\n"
                        f"{call_estrategia}\n"
                    )
                    enviar_alerta_telegram(msg)
                    alertas_enviados.append(id_jogo)

        except Exception:
            pass

# Loops paralelos do sistema na Nuvem
def loop_da_escuta_comandos():
    while True:
        processar_comandos_telegram()
        time.sleep(1)  # Verifica se você digitou algum comando a cada 1 segundo

def loop_do_monitor_live():
    print("🟢 Central Interativa v8 Ligada na Nuvem...")
    enviar_alerta_telegram("⚙️ *Central v8 Interativa Online!* Comandos liberados:\n\n"
                            "👉 Digite `/aovivo` para ver o painel de jogos ativos.\n"
                            "👉 Digite `/jogo Nome do Jogo` para cadastrar pré-jogo.\n"
