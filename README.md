
# Guia de Configuração do Webhook para Alphabot API

## **Visão Geral**

Este guia descreve como configurar e executar o webhook em Python que processa eventos do **Alphabot API**, como `raffle:created`, `raffle:edited` e `raffle:active`. O webhook valida os eventos recebidos, gerencia inscrições automáticas e respeita os limites de taxa (rate limit) da API.

---

## **Passo 1: Pré-requisitos**

### **Software Necessário**
- Python 3.6+
- Redis (opcional, para controle centralizado de concorrência)
- Servidor Linux com acesso root

### **Dependências Python**
Instale os pacotes necessários com:
```bash
pip install flask requests python-dotenv
```

---

## **Passo 2: Configurar o Projeto**

### **1. Clonar o Repositório**
Clone o repositório ou copie o código:
```bash
git clone https://github.com/DaemonBSD/webhook_alphabot.git
cd webhook
```

### **2. Criar o Ambiente Virtual**
Configure um ambiente Python isolado:
```bash
python3 -m venv webhook_env
source webhook_env/bin/activate
```

### **3. Instalar Dependências**
```bash
pip install -r requirements.txt
```

### **4. Configurar Variáveis de Ambiente**
Crie um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
```env
ALPHABOT_API_KEY=sua_chave_api_aqui
```

---

## **Passo 3: Testar o Webhook Localmente**
Execute o script para testar o webhook:
```bash
python3 webhook_with_rate_limit.py
```
O webhook estará acessível em `http://<seu_ip>:5000/webhook`.

Use ferramentas como `curl` ou Postman para simular requisições ao webhook.

---

## **Passo 4: Implantar com Gunicorn**

### **1. Instalar Gunicorn**
```bash
pip install gunicorn
```

### **2. Executar com Gunicorn**
Inicie o Gunicorn manualmente:
```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 webhook_with_rate_limit:app
```

---

## **Passo 5: Automatizar com `systemd`**

### **1. Criar o Arquivo de Serviço**
Edite o arquivo de serviço:
```bash
sudo nano /etc/systemd/system/webhook.service
```
Adicione o seguinte conteúdo:
```ini
[Unit]
Description=Webhook Service
After=network.target

[Service]
User=seu_usuario
WorkingDirectory=/caminho/para/webhook
ExecStart=/caminho/para/webhook/webhook_env/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 webhook_with_rate_limit:app
Restart=always
EnvironmentFile=/caminho/para/webhook/.env

[Install]
WantedBy=multi-user.target
```

### **2. Habilitar e Iniciar o Serviço**
Ative e inicie o serviço para execução contínua:
```bash
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook
```

### **3. Monitorar Logs**
Verifique os logs do serviço:
```bash
journalctl -u webhook.service -f
```

---

## **Passo 6: Testar Inscrição em Raffles**
Certifique-se de que o webhook está funcionando corretamente enviando eventos simulados.

Exemplo de teste com `curl`:
```bash
curl -X POST http://localhost:5000/webhook -H "Content-Type: application/json" -d '{
    "event": "raffle:created",
    "timestamp": "1234567890",
    "hash": "simulated_hash",
    "data": {
        "raffle": {
            "slug": "example-raffle"
        }
    }
}'
```

---

## **Funcionalidades do Webhook**

### **1. Segurança**
- O webhook valida a autenticidade das requisições usando HMAC SHA256.

### **2. Gerenciamento de Rate Limit**
- Lida com respostas `429` usando **retry com backoff exponencial**.

### **3. Controle de Concorrência (Opcional)**
- Use Redis para evitar duplicidade no processamento de eventos simultâneos.

---

## **Conclusão**

Agora você tem um webhook funcional para processar eventos do Alphabot API de forma segura e escalável. Use este guia para configurar, testar e monitorar sua aplicação no Linux. 🚀
