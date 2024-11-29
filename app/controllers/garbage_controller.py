import requests
from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
import json
import os
import RPi.GPIO as GPIO
import time

# Configuração do GPIO
GPIO.setmode(GPIO.BOARD)  # Use o modo BOARD (números físicos dos pinos)
GPIO.setwarnings(False)

# Pinos dos LEDs
LED_VERMELHO = 11
LED_VERDE = 12
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(LED_VERDE, GPIO.OUT)

# Inicializa os LEDs desligados
GPIO.output(LED_VERMELHO, GPIO.LOW)
GPIO.output(LED_VERDE, GPIO.LOW)

# Pinos do sensor HC-SR04
TRIG = 15
ECHO = 16
ALTURA_LIXEIRA = 20.0  # Altura máxima da lixeira em cm
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Configuração do blueprint
garbage_bp = Blueprint("garbage", __name__)

# Arquivos de persistência
STATE_FILE = "state.json"
HISTORY_FILE = "history.json"

# Configuração do ThingSpeak
THINGSPEAK_API_KEY = "4UU0PT3X0CXEBMCC"
THINGSPEAK_URL = "https://api.thingspeak.com/update"

# Funções de persistência
def load_state():
    """Carrega o estado da lixeira do arquivo JSON."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as file:
            return json.load(file)
    return {"status": "disponível", "ocupacao": 0}

def save_state(state):
    """Salva o estado da lixeira no arquivo JSON."""
    with open(STATE_FILE, "w") as file:
        json.dump(state, file)

def load_history():
    """Carrega o histórico de eventos do arquivo JSON."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            return json.load(file)
    return []

def save_history(history):
    """Salva o histórico de eventos no arquivo JSON."""
    with open(HISTORY_FILE, "w") as file:
        json.dump(history, file)

# Estado inicial e histórico
garbage_state = load_state()
event_history = load_history()

# Função para medir a ocupação da lixeira
def medir_ocupacao():
    """Mede o nível de ocupação da lixeira usando o HC-SR04."""
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    inicio = time.time()
    fim = time.time()

    # Aguarda o pulso de início (LOW para HIGH)
    timeout_inicio = time.time() + 1  # Timeout de 1 segundo
    while GPIO.input(ECHO) == GPIO.LOW:
        inicio = time.time()
        if time.time() > timeout_inicio:  # Timeout
            print("Erro: Timeout ao aguardar o pulso inicial.")
            return 0  # Retorna ocupação 0 em caso de erro

    # Aguarda o pulso de fim (HIGH para LOW)
    timeout_fim = time.time() + 1  # Timeout de 1 segundo
    while GPIO.input(ECHO) == GPIO.HIGH:
        fim = time.time()
        if time.time() > timeout_fim:  # Timeout
            print("Erro: Timeout ao aguardar o pulso final.")
            return 0  # Retorna ocupação 0 em caso de erro

    # Calcula o tempo de ida e volta do pulso
    duracao = fim - inicio
    distancia = (duracao * 34300) / 2  # Distância em cm

    # Calcula o percentual de ocupação
    ocupacao = max(0, min(100, 100 - (distancia / ALTURA_LIXEIRA) * 100))
    print(f"Distância: {distancia} cm, Ocupação: {ocupacao}%")  # Debug
    return round(ocupacao)

# Função para piscar LEDs
def piscar_led(led_pin, vezes, intervalo):
    """Pisca o LED especificado um número de vezes."""
    for _ in range(vezes):
        GPIO.output(led_pin, GPIO.HIGH)
        time.sleep(intervalo)
        GPIO.output(led_pin, GPIO.LOW)
        time.sleep(intervalo)

# Controle dos LEDs
def atualizar_leds():
    """Atualiza os LEDs com base no estado da lixeira."""
    if garbage_state["status"] == "cheia":
        GPIO.output(LED_VERDE, GPIO.LOW)
        GPIO.output(LED_VERMELHO, GPIO.HIGH)
    else:
        GPIO.output(LED_VERMELHO, GPIO.LOW)
        GPIO.output(LED_VERDE, GPIO.HIGH)

# Rotas do Flask
@garbage_bp.route("/")
def index():
    """Página inicial."""
    return render_template("index.html")

@garbage_bp.route("/update", methods=["GET"])
def update_state():
    """Atualiza o estado da lixeira, envia para o ThingSpeak e adiciona ao histórico."""
    global garbage_state
    ocupacao_atual = medir_ocupacao()  # Chama a função para medir a ocupação
    garbage_state["ocupacao"] = ocupacao_atual
    garbage_state["status"] = "cheia" if ocupacao_atual > 80 else "disponível"

    # Atualiza LEDs e salva o estado
    atualizar_leds()
    save_state(garbage_state)

    # Adiciona o evento ao histórico
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    event = {
        "date": timestamp,
        "ocupacao": garbage_state["ocupacao"],
        "status": garbage_state["status"]
    }
    event_history.append(event)
    save_history(event_history)  # Salva o histórico atualizado

    # Envia os dados para o ThingSpeak
    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": garbage_state["ocupacao"]  # A ocupação é enviada para o campo 1
    }
    try:
        response = requests.post(THINGSPEAK_URL, data=payload)
        if response.status_code == 200:
            print("Dados enviados ao ThingSpeak com sucesso!")
        else:
            print(f"Erro ao enviar dados: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Erro ao conectar ao ThingSpeak: {e}")

    return jsonify(garbage_state)

@garbage_bp.route("/history", methods=["GET"])
def get_history():
    """Retorna o histórico de eventos."""
    return jsonify(event_history)

@garbage_bp.route("/clear_history", methods=["POST"])
def clear_history():
    """Limpa o histórico de eventos."""
    global event_history
    event_history = []  # Limpa o histórico em memória
    save_history(event_history)  # Limpa o arquivo JSON
    return jsonify({"message": "Histórico limpo com sucesso!"})

@garbage_bp.route("/control_tampa/<action>", methods=["POST"])
def control_tampa(action):
    """Controla a abertura e fechamento da tampa."""
    global event_history
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if action == "abrir":
        if garbage_state["status"] == "disponível":
            piscar_led(LED_VERDE, 3, 0.3)  # Pisca o LED verde 3 vezes
        elif garbage_state["status"] == "cheia":
            piscar_led(LED_VERMELHO, 3, 0.3)  # Pisca o LED vermelho 3 vezes
        event_history.append({"date": timestamp, "event": "Tampa aberta"})
    elif action == "fechar":
        event_history.append({"date": timestamp, "event": "Tampa fechada"})

    save_history(event_history)  # Salva o histórico
    return jsonify({"message": f"Tampa {action} com sucesso!"})

