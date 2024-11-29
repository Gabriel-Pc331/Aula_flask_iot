                     Sistema de Monitoramento de Lixeira Inteligente

Este projeto visa monitorar o nível de ocupação de uma lixeira utilizando um sensor ultrassônico, LEDs para sinalização e uma interface web com Flask. A ocupação também é enviada para o ThingSpeak para análise remota.

Funcionalidades Principais
1. Medir Ocupação
A função medir_ocupacao() utiliza o sensor ultrassônico HC-SR04 para calcular a distância até a tampa da lixeira e converte isso em um percentual de ocupação.

```python
def medir_ocupacao():
    GPIO.output(TRIG, GPIO.HIGH)
    time.sleep(0.00001)
    GPIO.output(TRIG, GPIO.LOW)

    while GPIO.input(ECHO) == GPIO.LOW:
        inicio = time.time()
    while GPIO.input(ECHO) == GPIO.HIGH:
        fim = time.time()

    duracao = fim - inicio
    distancia = (duracao * 34300) / 2  # Fórmula para calcular a distância em cm
    ocupacao = max(0, min(100, 100 - (distancia / ALTURA_LIXEIRA) * 100))
    return round(ocupacao)

2. Atualizar LEDs
Dependendo do estado da lixeira (disponível ou cheia), os LEDs são acionados para indicar o status.

```python
def atualizar_leds():
    if garbage_state["status"] == "cheia":
        GPIO.output(LED_VERDE, GPIO.LOW)
        GPIO.output(LED_VERMELHO, GPIO.HIGH)
    else:
        GPIO.output(LED_VERMELHO, GPIO.LOW)
        GPIO.output(LED_VERDE, GPIO.HIGH)

3. Rota para Atualizar Estado
A rota /update mede a ocupação da lixeira, atualiza o estado e envia os dados para o ThingSpeak.


@garbage_bp.route("/update", methods=["GET"])
def update_state():
    ocupacao_atual = medir_ocupacao()  # Medição de ocupação
    garbage_state["ocupacao"] = ocupacao_atual
    garbage_state["status"] = "cheia" if ocupacao_atual > 80 else "disponível"

    atualizar_leds()  # Atualiza os LEDs
    save_state(garbage_state)  # Salva o estado

    payload = {
        "api_key": THINGSPEAK_API_KEY,
        "field1": garbage_state["ocupacao"]
    }
    requests.post(THINGSPEAK_URL, data=payload)

    return jsonify(garbage_state)

4. Controle da Tampa
Permite controlar a tampa da lixeira (abrir ou fechar) através da rota /control_tampa/<action>.


@garbage_bp.route("/control_tampa/<action>", methods=["POST"])
def control_tampa(action):
    if action == "abrir":
        piscar_led(LED_VERDE, 3, 0.3)
    elif action == "fechar":
        piscar_led(LED_VERMELHO, 3, 0.3)
    return jsonify({"message": f"Tampa {action} com sucesso!"})