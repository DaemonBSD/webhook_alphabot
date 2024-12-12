
import os
import logging
import hmac
import hashlib
import json
import time
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações da API do Alphabot
ALPHABOT_API_BASE_URL = "https://api.alphabot.app/v1"
API_KEY = os.getenv('ALPHABOT_API_KEY')

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def verify_webhook(event, timestamp, provided_hash):
    """
    Verifica a autenticidade do webhook usando HMAC SHA256
    """
    try:
        message = f"{event}\n{timestamp}"
        hmac_obj = hmac.new(
            API_KEY.encode('utf-8'), 
            message.encode('utf-8'), 
            hashlib.sha256
        )
        calculated_hash = hmac_obj.hexdigest()
        logger.debug(f"Evento: {event}")
        logger.debug(f"Timestamp: {timestamp}")
        logger.debug(f"Hash recebido: {provided_hash}")
        logger.debug(f"Hash calculado: {calculated_hash}")
        return hmac.compare_digest(calculated_hash, provided_hash)
    except Exception as e:
        logger.error(f"Erro na verificação do webhook: {e}")
        return False

@app.route('/webhook', methods=['POST'])
def handle_webhook():
    try:
        raw_payload = request.get_data().decode('utf-8')
        logger.info(f"Payload bruto recebido: {raw_payload}")
        payload = request.json

        if not payload:
            logger.warning("Payload vazio ou inválido")
            return jsonify({"status": "error", "message": "Payload inválido"}), 400

        event = payload.get('event')
        timestamp = payload.get('timestamp')
        webhook_hash = payload.get('hash')
        data = payload.get('data', {})

        if not verify_webhook(event, timestamp, webhook_hash):
            logger.warning(f"Hash inválido recebido para o evento: {event}")
            return jsonify({"status": "error", "message": "Hash inválido"}), 400

        if event in ['raffle:created', 'raffle:edited', 'raffle:active']:
            raffle = data.get('raffle', {})
            raffle_slug = raffle.get('slug')

            if raffle_slug:
                inscription_response = subscribe_to_raffle_with_retry(raffle_slug)
                if inscription_response:
                    logger.info(f"Inscrição na raffle {raffle_slug} realizada com sucesso")
                else:
                    logger.error(f"Falha ao inscrever na raffle {raffle_slug}")

        logger.info(f"Webhook recebido - Evento: {event}")
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

def subscribe_to_raffle_with_retry(raffle_slug, max_retries=3):
    """
    Inscrever-se em uma raffle com suporte a retry em caso de rate limit.
    """
    endpoint = f"{ALPHABOT_API_BASE_URL}/register"
    payload = {"slug": raffle_slug}

    for attempt in range(max_retries):
        try:
            logger.info(f"Tentando registrar na raffle: {raffle_slug} (tentativa {attempt + 1})")
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 10))
                logger.warning(f"Rate limit excedido. Aguardando {retry_after} segundos antes de tentar novamente...")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao registrar na raffle {raffle_slug}: {e}")
            if attempt == max_retries - 1:
                logger.error("Máximo de tentativas atingido. Falha ao inscrever na raffle.")

    return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
