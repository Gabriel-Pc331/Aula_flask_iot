Sistema de Monitoramento de Lixeira Inteligente
Este projeto implementa um sistema inteligente para monitorar o nível de ocupação de uma lixeira. Ele utiliza sensores ultrassônicos para realizar medições, LEDs para sinalização visual e uma interface web desenvolvida com Flask. O sistema também é integrado ao ThingSpeak para armazenamento e análise dos dados coletados.

Estrutura do Código
1. Configuração do Hardware
GPIO:
Configurado para operar no modo BOARD, que utiliza os números físicos dos pinos do Raspberry Pi.
LEDs:
Verde: Indica que a lixeira está disponível.
Vermelho: Indica que a lixeira está cheia.
Sensor HC-SR04:
Responsável por medir a distância do lixo até a tampa da lixeira para determinar o nível de ocupação.
2. Integração com ThingSpeak
Chave de API:
Configurada para envio de dados para a plataforma ThingSpeak.
Envio de Dados:
Realizado por meio de requisições POST, enviando os dados de ocupação em tempo real.
Detalhamento do Código
Configuração Inicial
Nesta seção, os pinos GPIO e LEDs são configurados e inicializados.

python
Copiar código
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)  # Configuração para usar os números físicos dos pinos
GPIO.setwarnings(False)

# Configuração dos LEDs
LED_VERMELHO = 11
LED_VERDE = 12
GPIO.setup(LED_VERMELHO, GPIO.OUT)
GPIO.setup(LED_VERDE, GPIO.OUT)

# Inicializa os LEDs como desligados
GPIO.output(LED_VERMELHO, GPIO.LOW)
GPIO.output(LED_VERDE, GPIO.LOW)
Medição de Ocupação
A função abaixo utiliza o sensor ultrassônico HC-SR04 para calcular o percentual de ocupação da lixeira com base na altura da lixeira e na distância medida.

python
Copiar código
def medir_ocupacao():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    # Aguarda os pulsos do sensor
    while GPIO.input(ECHO) == GPIO.LOW:
        inicio = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        fim = time.time()

    # Calcula a distância com base no tempo do pulso
    duracao = fim - inicio
    distancia = (duracao * 34300) / 2  # Fórmula para calcular a distância em cm

    # Converte a distância em ocupação percentual
    ocupacao = max(0, min(100, 100 - (distancia / ALTURA_LIXEIRA) * 100))
    return round(ocupacao)
Controle de LEDs
A função atualiza os LEDs com base no estado da lixeira (disponível ou cheia).

python
Copiar código
def atualizar_leds():
    if garbage_state["status"] == "cheia":
        GPIO.output(LED_VERDE, GPIO.LOW)
        GPIO.output(LED_VERMELHO, GPIO.HIGH)
    else:
        GPIO.output(LED_VERMELHO, GPIO.LOW)
        GPIO.output(LED_VERDE, GPIO.HIGH)
Rotas do Flask
O sistema expõe rotas REST para interação com a aplicação.

1. Rota Principal (/)
Exibe a interface inicial do sistema.

python
Copiar código
@garbage_bp.route("/")
def index():
    return render_template("index.html")
2. Atualizar Estado (/update)
Mede o nível de ocupação, atualiza o estado da lixeira e envia os dados para o ThingSpeak.

python
Copiar código
@garbage_bp.route("/update", methods=["GET"])
def update_state():
    ocupacao_atual = medir_ocupacao()
    garbage_state["ocupacao"] = ocupacao_atual
    garbage_state["status"] = "cheia" if ocupacao_atual > 80 else "disponível"

    atualizar_leds()  # Atualiza os LEDs
    save_state(garbage_state)  # Salva o estado

    # Envia os dados para o ThingSpeak
    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": garbage_state["ocupacao"]
    }
    requests.post(THINGSPEAK_URL, data=payload)

    return jsonify(garbage_state)
3. Histórico de Eventos (/history)
Retorna o histórico de eventos registrados.

python
Copiar código
@garbage_bp.route("/history", methods=["GET"])
def get_history():
    return jsonify(event_history)
4. Controle da Tampa (/control_tampa/<action>)
Permite abrir ou fechar a tampa da lixeira.

python
Copiar código
@garbage_bp.route("/control_tampa/<action>", methods=["POST"])
def control_tampa(action):
    if action == "abrir":
        piscar_led(LED_VERDE, 3, 0.3)
    elif action == "fechar":
        piscar_led(LED_VERMELHO, 3, 0.3)
    return jsonify({"message": f"Tampa {action} com sucesso!"})
Principais Funcionalidades
Medição de Ocupação:
Mede a ocupação da lixeira com base na altura total e na distância calculada pelo sensor ultrassônico.
Indicação com LEDs:
Exibe o status da lixeira (disponível ou cheia) com LEDs de diferentes cores.
Registro de Histórico:
Armazena eventos, como abertura e fechamento da tampa, em um arquivo JSON.
Integração com ThingSpeak:
Envia os dados de ocupação para uma plataforma na nuvem para monitoramento remoto.
Interface com Flask:
Permite monitoramento e controle da lixeira por meio de rotas REST.