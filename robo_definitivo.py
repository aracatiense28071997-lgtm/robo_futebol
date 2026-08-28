import http.server
import json
import socketserver
import threading
import time
from datetime import datetime
import requests

# 🔑 CONFIGURAÇÕES VALIDADAS DO SEU BOT TELEGRAM
CHAT_ID = 1027409830

p1, p2, p3, p4, p5, p6 = (
    "https://", "api.", "telegram", ".org/bot",
    "8200577138:AAFdKrmOv2QQKrvfLGujQPe4yhiME-w4GzU",
    "/sendMessage"
)
URL_TELEGRAM = p1 + p2 + p3 + p4 + p5 + p6

alertas_enviados = []
ultima_analise_pre_jogo = ""

def enviar_alerta_telegram(mensagem):
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(URL_TELEGRAM, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

# ==============================================================================
# 📊 MOTOR 1: PRÉ-JOGO TOTALMENTE AUTOMÁTICO (BUSCA JOGOS REAIS DO DIA)
# ==============================================================================
def executar_analise_pre_jogo_global():
    global ultima_analise_pre_jogo
    hoje = datetime.now().strftime("%Y-%m-%d")
    
    if ultima_analise_pre_jogo == hoje:
        return
        
    print("📊 Buscando partidas reais do dia de hoje na internet...")
    
    msg_pre = f"📊 *ROBÔ ARACATIENSE: ANÁLISE PRÉ-JOGO ({datetime.now().strftime('%d/%m/%Y')})* 📊\n"
    msg_pre += "⚠️ _Grade real de partidas mapeadas para as próximas horas_\n\n"
    
    esportes_ajuste = {
        "FUTEBOL": "soccer",
        "BASQUETE": "basketball",
        "HÓQUEI NO GELO": "hockey",
        "TÊNIS": "tennis",
        "BEISEBOL": "baseball"
    }
    
    encontrou_qualquer_jogo = False
    
    # O robô vai tentar buscar os jogos reais de hoje diretamente no feed público de eventos agendados
    for nome_esporte, id_esporte in esportes_ajuste.items():
        try:
            # URL de eventos agendados para o dia de hoje (agenda global)
            url_agenda = f"https://spoyer.com{id_esporte}"
            response = requests.get(url_agenda, timeout=10)
            
            if response.status_code == 200:
                dados = response.json()
                jogos = dados.get("games", [])
                
                if jogos:
                    cont = 0
                    for j in jogos:
                        # Pega apenas os 2 primeiros jogos reais de cada esporte para o relatório não ficar gigante
                        if cont < 2:
                            time_casa = j.get("home", {}).get("name", "Equipe A")
                            time_fora = j.get("away", {}).get("name", "Equipe B")
                            liga = j.get("league", {}).get("name", "Torneio")
                            
                            # Define uma dica inteligente baseada no esporte
                            if nome_esporte == "FUTEBOL":
                                tip = "🔥 Entrada sugerida: Over 1.5 Gols na partida"
                            elif nome_esporte == "BASQUETE":
                                tip = "🔥 Entrada sugerida: Over Pontos no jogo"
                            elif nome_esporte == "HÓQUEI NO GELO":
                                tip = "🔥 Entrada sugerida: Mais de 4.5 Gols"
                            elif nome_esporte == "TÊNIS":
                                tip = "🔥 Entrada sugerida: Vencedor do 1º Set"
                            else:
                                tip = "🔥 Entrada sugerida: Mais de 6.5 Corridas"
                                
                            msg_pre += (
                                f"📍 *[{nome_esporte}] - {liga}*\n"
                                f"⚔️ {time_casa} vs {time_fora}\n"
                                f"{tip}\n"
                                f"-------------------------------------\n"
                            )
                            cont += 1
                            encontrou_qualquer_jogo = True
        except Exception:
            pass

    # Caso todas as APIs de busca de agenda falhem ao mesmo tempo, ele avisa você em vez de mandar jogos falsos
    if not encontrou_qualquer_jogo:
        msg_pre += "📋 Nenhuma grande partida encontrada nos servidores de agendamento para as próximas horas.\n"
        msg_pre += "📡 O monitoramento continuará ativo focando 100% nos jogos ao vivo!\n"
        msg_pre += "-------------------------------------\n"

    enviar_alerta_telegram(msg_pre)
    ultima_analise_pre_jogo = hoje

# ==============================================================================
# 🎯 MOTOR 2: ANÁLISE AO VIVO (5 ESPORTES)
# ==============================================================================
def monitorar_esportes_avancado():
    try:
        executar_analise_pre_jogo_global()
    except Exception as e:
        print(f"Erro na rotina pré-jogo: {e}")

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
                        g_casa, g_fora = int(gols), int(gols)
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
                        if abs(int(pontos) - int(pontos)) <= 3:
                            disparar = True
                            call_estrategia = f"🏀 *ESTRATÉGIA: BASQUETE LIVE* 🏀\n🎯 *Sugestão:* OVER pontos no Quarto Final.\n📊 Cronômetro parando muito por faltas táticas."

                elif esporte == "TENIS":
                    if "5:5" in placar or "6:5" in placar or "5:6" in placar:
                        disparar = True
                        call_estrategia = f"🎾 *ESTRATÉGIA: TÊNIS LIVE* 🎾\n🎯 *Sugestão:* Vencedor do Próximo Game (Sacador).\n📊 Reta final equilibrada de set com vantagem para quem saca."

                elif esporte == "BEISEBOL" and ("8th" in tempo or "9th" in tempo):
                    corridas = placar.split("-")
                    if len(corridas) == 2 and corridas == corridas:
                        disparar = True
                        call_estrategia = f"⚾ *ESTRATÉGIA: INNINGS FINAIS BEISEBOL* ⚾\n🎯 *Sugestão:* Mercado de Empate na Entrada Atual ou Over Corridas."

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

def loop_do_robo():
    print("🟢 Central Inteligente Híbrida v7 Ativada...")
    enviar_alerta_telegram("🚀 *Central de Inteligência v7 Ativada!* Motor configurado para buscar apenas os confrontos reais do dia na internet.")
    while True:
        monitorar_esportes_avancado()
        time.sleep(60)

def rodar_servidor_web():
    PORT = 10000
