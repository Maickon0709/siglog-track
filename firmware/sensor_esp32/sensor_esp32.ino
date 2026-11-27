// SIG-Log Track — firmware do sensor fisico (ESP32 + DHT22)
//
// Le temperatura/umidade e envia por HTTP para POST /sensor-readings do gateway.
// O sensor so conhece o proprio DEVICE_ID; carga, veiculo e viagem sao
// associados no gateway (POST /devices).
//
// Bibliotecas (Arduino IDE > Gerenciar bibliotecas):
//   - "DHT sensor library" (Adafruit) + "Adafruit Unified Sensor"
// Placa: "ESP32 Dev Module" (pacote esp32 da Espressif)

#include <WiFi.h>
#include <HTTPClient.h>
#include <time.h>
#include <DHT.h>
#include "config.h"

DHT dht(DHT_PINO, DHT_TIPO);
bool relogioOk = false;

void conectarWifi() {
  if (WiFi.status() == WL_CONNECTED) return;
  Serial.printf("Conectando em %s", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_SENHA);
  for (int i = 0; i < 40 && WiFi.status() != WL_CONNECTED; i++) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(WiFi.status() == WL_CONNECTED ? " ok" : " falhou");
  if (WiFi.status() == WL_CONNECTED) Serial.println(WiFi.localIP());
}

void sincronizarRelogio() {
  configTime(0, 0, "pool.ntp.org", "time.google.com");  // UTC
  struct tm t;
  relogioOk = getLocalTime(&t, 5000);
  Serial.println(relogioOk ? "Relogio NTP sincronizado" : "Sem NTP: gateway usa a hora dele");
}

// Escreve o timestamp ISO-8601 UTC em buf, ou "null" se o relogio nao sincronizou.
void timestampJson(char *buf, size_t n) {
  struct tm t;
  if (relogioOk && getLocalTime(&t, 10)) {
    strftime(buf, n, "\"%Y-%m-%dT%H:%M:%SZ\"", &t);
  } else {
    snprintf(buf, n, "null");
  }
}

int lerBateria() {
#if BATERIA_PINO >= 0
  float v = analogReadMilliVolts(BATERIA_PINO) / 1000.0 * BATERIA_DIVISOR;
  int pct = (int)((v - BATERIA_V_MIN) / (BATERIA_V_MAX - BATERIA_V_MIN) * 100.0);
  return constrain(pct, 0, 100);
#else
  return -1;
#endif
}

void enviarLeitura(float temperatura, float umidade, int bateria) {
  char ts[32], umid[16], bat[8], pos[64];
  timestampJson(ts, sizeof(ts));
  if (isnan(umidade)) snprintf(umid, sizeof(umid), "null");
  else snprintf(umid, sizeof(umid), "%.1f", umidade);
  if (bateria < 0) snprintf(bat, sizeof(bat), "null");
  else snprintf(bat, sizeof(bat), "%d", bateria);
#if USAR_POSICAO_FIXA
  snprintf(pos, sizeof(pos), "\"latitude\":%.6f,\"longitude\":%.6f", LATITUDE_FIXA, LONGITUDE_FIXA);
#else
  snprintf(pos, sizeof(pos), "\"latitude\":null,\"longitude\":null");
#endif

  char corpo[320];
  snprintf(corpo, sizeof(corpo),
           "{\"deviceId\":\"%s\",\"temperatura\":%.2f,\"umidade\":%s,"
           "\"bateria\":%s,%s,\"timestamp\":%s}",
           DEVICE_ID, temperatura, umid, bat, pos, ts);

  HTTPClient http;
  http.begin(GATEWAY_URL);
  http.setTimeout(5000);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-Device-Key", DEVICE_API_KEY);
  int status = http.POST(corpo);
  Serial.printf("POST %d  %s\n", status, corpo);
  if (status != 202) Serial.println(http.getString());
  http.end();
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  conectarWifi();
  if (WiFi.status() == WL_CONNECTED) sincronizarRelogio();
}

void loop() {
  conectarWifi();

  float temperatura = dht.readTemperature();
  float umidade = dht.readHumidity();

  if (isnan(temperatura)) {
    // Sem leitura valida nao envia nada: se persistir, o gateway gera DispositivoOffline.
    Serial.println("Falha ao ler o DHT: verifique fios e resistor de pull-up");
  } else if (WiFi.status() == WL_CONNECTED) {
    if (!relogioOk) sincronizarRelogio();
    enviarLeitura(temperatura, umidade, lerBateria());
  }

  delay(INTERVALO_MS);
}
