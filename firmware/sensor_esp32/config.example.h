// Copie este arquivo para config.h e preencha. config.h nao vai para o Git.
#pragma once

// Wi-Fi
#define WIFI_SSID      "NOME_DA_REDE"
#define WIFI_SENHA     "SENHA_DA_REDE"

// Gateway do SIG-Log Track (IP do computador que roda o docker compose)
#define GATEWAY_URL    "http://192.168.0.10:8000/sensor-readings"
#define DEVICE_API_KEY "troque-esta-chave"   // igual a DEVICE_API_KEY do gateway

// Identificacao do sensor (cadastrado no POST /devices)
#define DEVICE_ID      "IOT-001"

// Sensor DHT22 (temperatura + umidade)
#define DHT_PINO       4
#define DHT_TIPO       DHT22                 // troque para DHT11 se usar o DHT11

// Bateria: pino ADC ligado a um divisor de tensao. -1 = nao medir.
#define BATERIA_PINO   -1
#define BATERIA_V_MIN  3.3                   // tensao = 0 %
#define BATERIA_V_MAX  4.2                   // tensao = 100 %
#define BATERIA_DIVISOR 2.0                  // fator do divisor (2 resistores iguais = 2.0)

// GPS: sem modulo GPS, envia posicao fixa. Use 0 para nao enviar posicao.
#define USAR_POSICAO_FIXA 1
#define LATITUDE_FIXA  -23.5505
#define LONGITUDE_FIXA -46.6333

// Intervalo entre leituras (ms). DHT22 precisa de pelo menos 2000.
#define INTERVALO_MS   10000
