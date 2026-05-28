import os
import threading
import time
import datetime
from http.server import SimpleHTTPRequestHandler, HTTPServer
import requests

# ==============================================================================
# 🔐 CONFIGURAÇÕES DE TELEGRAM E BANCA
# ==============================================================================
TELEGRAM_TOKEN = "8071742858:AAFasipn1Jo2gkHNgrSiSwfn-ZXm29fI7qw"
SEU_CHAT_ID = "2030461760"

# Valor total que você vai dividir entre as duas casas na hora da Surebet
BANCA_ALVO_OPERAÇÃO = 100.00 

# --- SERVIDOR SIMULADO PARA O RENDER ---
def run_mock_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHTTPRequestHandler)
    print(f"Servidor HTTP do Render ativo na porta {port}")
    server.serve_forever()

threading.Thread(target=run_mock_server, daemon=True).start()

# --- FUNÇÃO DE ALERTA DO TELEGRAM ---
def enviar_alerta_surebet(mensagem):
    try:
        url = f"https://telegram.org{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": SEU_CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
        print("Alerta de Surebet enviado ao Telegram!")
    except Exception as e:
        print(f"Erro ao falar com o Telegram: {e}")

# --- ENGENHARIA DE ARBITRAGEM (PRÉ-JOGO E AO VIVO) ---
def varrer_oportunidades_multi_casa(jogos_notificados):
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Procurando odds desreguladas (Pré-Jogo e Live)...")
    
    # Simulação de duas distorções: uma pré-jogo e outra ao vivo
    distorcoes_detectadas = [
        {
            "id": 223344,
            "partida": "Cruzeiro x Atlético-MG",
            "momento": "⏰ PRÉ-JOGO (Faltam 2 horas)",
            "casa_over": "Betano",
            "mercado_over": "Mais de 2.5 Gols",
            "odd_over": 2.20,
            "casa_under": "Betfair",
            "mercado_under": "Menos de 2.5 Gols",
            "odd_under": 2.05,
        },
        {
            "id": 556677,
            "partida": "São Paulo x Bahia",
            "momento": "⚽ AO VIVO (Rolando agora)",
            "casa_over": "Bet365",
            "mercado_over": "Mais de 1.5 Gols",
            "odd_over": 1.95,
            "casa_under": "VBet",
            "mercado_under": "Menos de 1.5 Gols",
            "odd_under": 2.25,
        }
    ]

    for jogo in distorcoes_detectadas:
        jogo_id = jogo["id"]
        if jogo_id in jogos_notificados:
            continue

        odd_over = jogo["odd_over"]
        odd_under = jogo["odd_under"]

        # 🧮 FÓRMULA MATEMÁTICA: (1/Over) + (1/Under)
        indice_arbitragem = (1 / odd_over) + (1 / odd_under)

        if indice_arbitragem < 1.00:
            lucro_liquido_percentual = (1 - indice_arbitragem) * 100
            
            # Divisão proporcional da banca
            retorno_garantido = BANCA_ALVO_OPERAÇÃO / indice_arbitragem
            investimento_over = retorno_garantido / odd_over
            investimento_under = retorno_garantido / odd_under

            # Mensagem com indicação se o jogo é pré-jogo ou ao vivo
            msg_sinal = (
                f"🚨 *SUREBET DETECTADA! ({jogo['momento']})*\n\n"
                f"⚽ *Jogo:* {jogo['partida']}\n"
                f"📈 *Retorno Garantido:* `{lucro_liquido_percentual:.2f}%` fixo\n\n"
                f"📊 *DIRETRIZ DE INVESTIMENTO (Banca R$ {BANCA_ALVO_OPERAÇÃO:.2f}):*\n"
                f"🟩 *Aposta OVER:* {jogo['casa_over']}\n"
                f"   • Mercado: {jogo['mercado_over']}\n"
                f"   • Odd: {odd_over} | Colocar: `R$ {investimento_over:.2f}`\n\n"
                f"🟥 *Aposta UNDER:* {jogo['casa_under']}\n"
                f"   • Mercado: {jogo['mercado_under']}\n"
                f"   • Odd: {odd_under} | Colocar: `R$ {investimento_under:.2f}`\n\n"
                f"🏁 _Lucro garantido! Seu retorno final será de R$ {retorno_garantido:.2f}!_"
            )

            enviar_alerta_surebet(msg_sinal)
            jogos_notificados.add(jogo_id)

def main():
    print("🤖 Robô de Surebet Pré-Jogo e Live Iniciado!")
    enviar_alerta_surebet("🚀 *ROBÔ MULTI-CASAS ONLINE:* Rastreamento de odds desreguladas (Pré-Jogo e Ao Vivo) ativado!")
    
    jogos_notificados = set()
    while True:
        try:
            varrer_oportunidades_multi_casa(jogos_notificados)
        except Exception as e:
            print(f"Aviso no rastreador: {e}")
        time.sleep(30)  # Varredura a cada 30 segundos

if __name__ == "__main__":
    main()
