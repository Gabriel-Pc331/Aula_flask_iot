                            
                                
                                Sistema de Monitoramento de Lixeira Inteligente

Este projeto visa criar uma lixeira inteligente que pode monitorar seu nível de ocupação e fornecer uma indicação visual, tudo controlado de forma simples e eficiente. Usando sensores ultrassônicos, LEDs e uma interface web construída com Flask, o sistema é capaz de monitorar o quanto a lixeira está cheia e até mesmo enviar os dados para a nuvem, usando a plataforma ThingSpeak.

Estrutura do Código
1. Configuração do Hardware
GPIO: O sistema está configurado para usar os pinos físicos do Raspberry Pi (modo BOARD).
LEDs: Temos dois LEDs — um verde, que indica que a lixeira está disponível, e um vermelho, que indica que ela está cheia.
Sensor HC-SR04: Utilizamos o sensor ultrassônico para medir a distância entre o lixo e a tampa, determinando assim o nível de ocupação da lixeira.

2. Integração com ThingSpeak
Chave de API: O sistema envia os dados de ocupação em tempo real para o ThingSpeak usando uma chave de API.
Envio de Dados: Isso é feito através de requisições POST, permitindo que a plataforma armazene e analise os dados de forma contínua.

Detalhamento do Código
1. Configuração Inicial
Aqui, os pinos GPIO e os LEDs são configurados para que o sistema possa interagir com o hardware corretamente.

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
2. Medição de Ocupação
A função medir_ocupacao() calcula o percentual de ocupação da lixeira, medindo a distância entre o lixo e a tampa. Esse valor é então convertido em uma porcentagem.

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
3. Controle de LEDs
A função atualizar_leds() ajusta os LEDs de acordo com o status da lixeira — se está cheia ou disponível.

python
Copiar código
def atualizar_leds():
    if garbage_state["status"] == "cheia":
        GPIO.output(LED_VERDE, GPIO.LOW)
        GPIO.output(LED_VERMELHO, GPIO.HIGH)
    else:
        GPIO.output(LED_VERMELHO, GPIO.LOW)
        GPIO.output(LED_VERDE, GPIO.HIGH)
4. Rotas do Flask
A interface web é construída com Flask, e as rotas permitem interagir com o sistema.

Rota Principal (/): Exibe a página inicial do sistema.
python
Copiar código
@garbage_bp.route("/")
def index():
    return render_template("index.html")
Atualizar Estado (/update): Mede o nível de ocupação, atualiza o estado da lixeira e envia os dados para o ThingSpeak.
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

## Histórico de Eventos (/history)
Retorna o histórico de eventos, como abertura e fechamento da tampa.

```python
@garbage_bp.route("/history", methods=["GET"])
def get_history():
    return jsonify(event_history)
Controle da Tampa (/control_tampa/<action>)
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
Medição de Ocupação: O sistema calcula o nível de ocupação da lixeira com base na altura e na distância medida pelo sensor ultrassônico.

Indicação com LEDs: Os LEDs mostram o status da lixeira (disponível ou cheia) em tempo real.
Registro de Histórico: Todos os eventos, como abertura e fechamento da tampa, são registrados em um arquivo JSON para referência futura.

Integração com ThingSpeak: Os dados de ocupação são enviados para a nuvem, permitindo o monitoramento remoto.
Interface com Flask: A interface web permite que você visualize o status da lixeira, controle a tampa e acesse o histórico de eventos.

