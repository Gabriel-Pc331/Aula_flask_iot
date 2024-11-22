import RPi.GPIO as gpio
import time as delay
from app import app
from flask import render_template

# Configuração do GPIO
gpio.setmode(gpio.BOARD)  # Modo BOARD para números físicos dos pinos
gpio.setwarnings(False)

# Pinos dos LEDs
ledVermelho, ledVerde = 11, 12
gpio.setup(ledVermelho, gpio.OUT)
gpio.setup(ledVerde, gpio.OUT)

# Estado inicial dos LEDs
gpio.output(ledVermelho, gpio.LOW)
gpio.output(ledVerde, gpio.LOW)

# Pinos do sensor HC-SR04
pin_t = 15  # TRIG
pin_e = 16  # ECHO
lixeira_v = 20.0  # Altura máxima da lixeira em cm

gpio.setup(pin_t, gpio.OUT)
gpio.setup(pin_e, gpio.IN)

# Função para medir a distância
def distancia():
    """Calcula a ocupação da lixeira usando o sensor HC-SR04."""
    gpio.output(pin_t, True)
    delay.sleep(0.00001)
    gpio.output(pin_t, False)
    
    tempo_i = delay.time()
    tempo_f = delay.time()
    
    while gpio.input(pin_e) == False:
        tempo_i = delay.time()
    while gpio.input(pin_e) == True:
        tempo_f = delay.time()
        
    tempo_d = tempo_f - tempo_i  # Tempo de ida e volta do pulso
    distancia = (tempo_d * 34300) / 2  # Distância em cm
    
    # Calcula o percentual de ocupação
    ocupacao = max(0, min(100, 100 - (distancia / lixeira_v) * 100))
    return round(ocupacao)

# Funções para controlar o estado dos LEDs
def piscar_led(led_pin, vezes, intervalo):
    """Pisca o LED especificado."""
    for _ in range(vezes):
        gpio.output(led_pin, gpio.HIGH)
        delay.sleep(intervalo)
        gpio.output(led_pin, gpio.LOW)
        delay.sleep(intervalo)

def status_led_vermelho():
    """Retorna o status do LED vermelho."""
    return 'LED vermelho ON' if gpio.input(ledVermelho) == gpio.HIGH else 'LED vermelho OFF'

def status_led_verde():
    """Retorna o status do LED verde."""
    return 'LED verde ON' if gpio.input(ledVerde) == gpio.HIGH else 'LED verde OFF'

# Rotas do Flask
@app.route("/")
def index():
    """Página inicial."""
    ocupacao_atual = distancia()
    status = "cheia" if ocupacao_atual > 80 else "disponível"

    # Controle automático dos LEDs
    if status == "cheia":
        gpio.output(ledVerde, gpio.LOW)
        gpio.output(ledVermelho, gpio.HIGH)
    else:
        gpio.output(ledVermelho, gpio.LOW)
        gpio.output(ledVerde, gpio.HIGH)

    templateData = {
        'ledRed': status_led_vermelho(),
        'ledGreen': status_led_verde(),
        'ocup_lixeira': f"{ocupacao_atual}%",
        'status_lixeira': status
    }
    return render_template('index.html', **templateData)

@app.route("/led_vermelho/<action>")
def led_vermelho(action):
    """Controla o LED vermelho manualmente."""
    if action == 'on':
        gpio.output(ledVermelho, gpio.HIGH)
    elif action == 'off':
        gpio.output(ledVermelho, gpio.LOW)

    templateData = {
        'ledRed': status_led_vermelho(),
        'ledGreen': status_led_verde()
    }
    return render_template('index.html', **templateData)

@app.route("/led_verde/<action>")
def led_verde(action):
    """Controla o LED verde manualmente."""
    if action == 'on':
        gpio.output(ledVerde, gpio.HIGH)
    elif action == 'off':
        gpio.output(ledVerde, gpio.LOW)

    templateData = {
        'ledRed': status_led_vermelho(),
        'ledGreen': status_led_verde()
    }
    return render_template('index.html', **templateData)

@app.route("/abrir_tampa")
def abrir_tampa():
    """Simula a abertura da tampa."""
    ocupacao_atual = distancia()
    status = "cheia" if ocupacao_atual > 80 else "disponível"

    # Piscar LEDs ao abrir tampa
    if status == "disponível":
        piscar_led(ledVerde, 3, 0.3)
    else:
        piscar_led(ledVermelho, 3, 0.3)

    templateData = {
        'ledRed': status_led_vermelho(),
        'ledGreen': status_led_verde(),
        'ocup_lixeira': f"{ocupacao_atual}%",
        'status_lixeira': status
    }
    return render_template('index.html', **templateData)
