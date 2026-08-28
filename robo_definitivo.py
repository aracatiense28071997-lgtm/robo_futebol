import http.server
import socketserver
import threading
import time
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

def enviar_alerta_telegram(mensagem):
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(URL_TELEGRAM, json=payload)
    except Exception as e:
        print(f"Erro Telegram: {e}")

def monitorar_ao_vivo_assertivo():
    esportes = {
        "FUTEBOL": "https://spoyer.com",
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

                if esporte == "FUTEBOL":
                    gols = placar.split(":")
                    if len(gols) == 2:
                        chutes_totais = int(jogo.get("shots_home", 0)) + int(jogo.get("shots_away", 0))
                        if "'" in tempo and int(tempo.replace("'", "")) >= 72 and gols[0] == gols[1] and chutes_totais >= 12:
                            disparar = True
                            call_estrategia = "🎯 *Estratégia:* Buscar Gol no Final (Over Limite) ou Escanteio Asiático."

                if disparar:
                    msg = (
                        f"🔥 *ALERTA DE ALTA ASSERTIVIDADE* 🔥\n\n"
                        f"📊 *Modalidade:* {esporte}\n"
                        f"🏆 *Liga:* {liga}\n"
                        f"⚔️ *Confronto:* {time_casa} vs {time_fora}\n"
                        f"📈 *Placar Ao Vivo:* {placar} ({tempo})\n\n"
                        f"{call_estrategia}\n"
                    )
                    enviar_alerta_telegram(msg)
                    alertas_enviados.append(id_jogo)
        except Exception:
            pass

# 🔄 Loop principal do robô de futebol
def loop_do_robo():
    print("🟢 Monitoramento de Filtros Avançados ativado...")
    enviar_alerta_telegram("🎯 *Robô Aracatiense 24h Ativado na Nuvem!*")
    while True:
        monitorar_ao_vivo_assertivo()
        time.sleep(60)

# 🌐 Servidor Web Web fictício exigido pela Nuvem do Render
def rodar_servidor_web():
    PORT = 10000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Servidor Web ativo na porta {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Inicia o robô em segundo plano
    threading.Thread(target=loop_do_robo, daemon=True).start()
    # Inicia o servidor exigido pela nuvem na linha principal
    rodar_servidor_web()
