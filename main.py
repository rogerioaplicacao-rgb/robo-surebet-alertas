import os
import threading
import time
import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import requests

# ==============================================================================
# 🔐 CONFIGURAÇÕES DE API, TELEGRAM E BANCA
# ==============================================================================
API_FOOTBALL_KEY = "8bb27bbe8a02bfaa26fce895168daeb6"
TELEGRAM_TOKEN = "8071742858:AAFasipn1Jo2gkHNgrSiSwfn-ZXm29fI7qw"
SEU_CHAT_ID = "2030461760"

BANCA_ALVO_OPERAÇÃO = 100.00 

CASAS_PERMITIDAS = {
    1: "Bet365",
    12: "Betano",
    14: "VBet"
}

# --- FUNÇÃO DE ALERTA DO TELEGRAM ---
def enviar_alerta_surebet(mensagem):
    try:
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": SEU_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"Erro na API do Telegram: Code {response.status_code}")
    except Exception as e:
        print(f"Erro ao falar com o Telegram: {e}")

# --- FILTRO E TRATAMENTO DOS DADOS DA API-FOOTBALL ---
def processar_odds_reais(fixtures_dados, jogos_notificados):
    for item in fixtures_dados.get("response", []):
        fixture_id = item["fixture"]["id"]
        
        if fixture_id in jogos_notificados:
            continue

        partida = f"{item['fixture']['home']['name']} x {item['fixture']['away']['name']}"
        status_jogo = item["fixture"]["status"]["short"]
        momento = "⚽ AO VIVO" if status_jogo in ["1H", "2H", "HT"] else "⏰ PRÉ-JOGO"
        
        bookmakers = item.get("bookmakers", [])
        
        melhor_casa_1 = {"casa": None, "odd": 0.0}
        melhor_casa_x = {"casa": None, "odd": 0.0}
        melhor_casa_2 = {"casa": None, "odd": 0.0}
        vbet_participando = False

        for bookmaker in bookmakers:
            b_id = bookmaker["id"]
            if b_id not in CASAS_PERMITIDAS:
                continue
            
            nome_casa = CASAS_PERMITIDAS[b_id]
            if nome_casa == "VBet":
                vbet_participando = True

            for market in bookmaker.get("bets", []):
                if market["id"] == 1:
                    for val in market["values"]:
                        odd_valor = float(val["odd"])
                        if val["value"] == "Home" and odd_valor > melhor_casa_1["odd"]:
                            melhor_casa_1 = {"casa": nome_casa, "odd": odd_valor}
                        elif val["value"] == "Draw" and odd_valor > melhor_casa_x["odd"]:
                            melhor_casa_x = {"casa": nome_casa, "odd": odd_valor}
                        elif val["value"] == "Away" and odd_valor > melhor_casa_2["odd"]:
                            melhor_casa_2 = {"casa": nome_casa, "odd": odd_valor}

        casas_selecionadas = [melhor_casa_1["casa"], melhor_casa_x["casa"], melhor_casa_2["casa"]]
        if "VBet" not in casas_selecionadas and not vbet_participando:
            continue

        if melhor_casa_1["odd"] > 0 and melhor_casa_x["odd"] > 0 and melhor_casa_2["odd"] > 0:
            indice_arbitragem = (1 / melhor_casa_1["odd"]) + (1 / melhor_casa_x["odd"]) + (1 / melhor_casa_2["odd"])

            if indice_arbitragem <= 1.0001:
                if abs(indice_arbitragem - 1.00) < 0.005:
                    tipo_alerta = "⚠️ PROTEÇÃO DE BANCA DETECTADA! (LUCRO ZERO)"
                    lucro_liquido_percentual = 0.00
                    retorno_garantido = BANCA_ALVO_OPERAÇÃO
                else:
                    tipo_alerta = "🚨 SUREBET 3-VIAS DETECTADA!"
                    lucro_liquido_percentual = ((1 / indice_arbitragem) - 1) * 100
                    retorno_garantido = BANCA_ALVO_OPERAÇÃO / indice_arbitragem

                inv_1 = retorno_garantido / melhor_casa_1["odd"]
                inv_x = retorno_garantido / melhor_casa_x["odd"]
                inv_2 = retorno_garantido / melhor_casa_2["odd"]
                tipo_mercado = "🚀 COM PAGAMENTO ANTECIPADO ATIVO (2 Gols)" if momento == "⏰ PRÉ-JOGO" else "⚠️ MERCADO SO (Sem Pagamento Antecipado / Live)"

                msg_sinal = (
                    f"{tipo_alerta}\nMomento: `{momento}`\nRegulamento: *{tipo_mercado}*\n\n"
                    f"⚽ *Jogo:* {partida}\n📈 *Retorno Previsto:* `{lucro_liquido_percentual:.2f}%` fixo\n\n"
                    f"📊 *DIRETRIZ DE INVESTIMENTO (Total R$ {BANCA_ALVO_OPERAÇÃO:.2f}):*\n"
                    f"🟩 *Vitória Casa (1):* {melhor_casa_1['casa']} | Odd: {melhor_casa_1['odd']} | Invista: `R$ {inv_1:.2f}`\n"
                    f"⬜ *Empate (X):* {melhor_casa_x['casa']} | Odd: {melhor_casa_x['odd']} | Invista: `R$ {inv_x:.2f}`\n"
                    f"🟥 *Vitória Fora (2):* {melhor_casa_2['casa']} | Odd: {melhor_casa_2['odd']} | Invista: `R$ {inv_2:.2f}`\n\n"
                    f"🏁 _Cenário Realizado! Seu retorno final será de R$ {retorno_garantido:.2f}_"
                )
                enviar_alerta_surebet(msg_sinal)
                jogos_notificados.add(fixture_id)

# --- REQUISIÇÃO À API-FOOTBALL ---
def varrer_oportunidades_multi_casa(jogos_notificados):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Conectando à API-Football...")
    url = "https://api-sports.io"
    data_hoje = datetime.datetime.now().strftime('%Y-%m-%d')
    params = {"date": data_hoje}
    headers = {"x-apisports-key": API_FOOTBALL_KEY}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            processar_odds_reais(response.json(), jogos_notificados)
        else:
            print(f"Erro API-Football: Status {response.status_code}")
    except Exception as e:
        print(f"Falha de conexão: {e}")

# --- LOOP DO BOT EM THREAD ---
def loop_principal_bot():
    print("Iniciando loop de varredura do Bot...")
    # Pequena espera para o servidor HTTP estar 100% ativo antes do primeiro alerta
    time.sleep(5)
    enviar_alerta_surebet("🚀 *ROBÔ PRODUÇÃO LIVE:* Conexão oficial com a API-Football estabelecida. Monitoramento de VBet, Bet365 e Betano iniciado.")
    
    jogos_notificados = set()
    while True:
        try:
            varrer_oportunidades_multi_casa(jogos_notificados)
        except Exception as e:
            print(f"Erro no loop principal: {e}")
        time.sleep(900)

if __name__ == "__main__":
    # 1. Iniciamos o loop do bot em segundo plano
    t = threading.Thread(target=loop_principal_bot, daemon=True)
    t.start()

    # 2. Travamos a linha principal rodando o Servidor HTTP exigido pelo Render (Garante a porta aberta imediatamente)
    port = int(os.environ.get("PORT", 10000))
    print(f"Servidor Web ativo para o Render na porta {port}")
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    server.serve_forever()
