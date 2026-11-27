# SIG-Log Track — Rastreamento de Cargas & Telemetria IoT (Squad 03)

Módulo da plataforma **SIG-Log** que responde: **"Onde está a carga?"** e **"A carga está dentro das condições adequadas?"**

Um sensor físico (ESP32 + DHT22/DHT11) envia temperatura, umidade, bateria e posição. O Track detecta as anomalias
e publica eventos no RabbitMQ para o **Fleet (Squad 02)**, o **Finance (Squad 04)** e o **CRM (Squad 06)**.

```
ESP32 + DHT22 ──HTTP──► SIG-Log Track ──RabbitMQ (siglog.events)──► Fleet · Finance · CRM
                              └── /metrics ──► Prometheus ──► Grafana
```

## Para os outros squads
Vocês **não precisam do nosso código**, só do contrato:
- Eventos: [`contracts/CONTRATO_EVENTOS.md`](contracts/CONTRATO_EVENTOS.md) + [`contracts/evento.schema.json`](contracts/evento.schema.json)
- API REST: [`contracts/openapi.yaml`](contracts/openapi.yaml)
- Consumidor de exemplo: [`scripts/consumidor.py`](scripts/consumidor.py)

## Rodando

### 1. Pré-requisitos (uma vez)
```bash
bash scripts/instalar_sistema.sh   # Docker + permissão na porta USB (pede sudo)
```
Depois saia da sessão e entre de novo.

### 2. Subir tudo
```bash
docker compose up --build
```
| Serviço | Endereço |
|---|---|
| API + OpenAPI | http://localhost:8000/docs |
| RabbitMQ | http://localhost:15672 (guest/guest) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) → pasta *SIG-Log* |

### 3. Vincular o sensor à carga
```bash
curl -X POST localhost:8000/devices -H 'Content-Type: application/json' \
  -d '{"deviceId":"IOT-001","shipmentId":"EXP-001","vehicleId":"VEI-042","tripId":"VIA-2026-0917","tipoCarga":"VACINA"}'
```
Faixas padrão: VACINA 2–8 °C · RESFRIADO 0–7 °C / ≤ 90 % · CONGELADO ≤ −18 °C · AMBIENTE 15–30 °C / ≤ 70 %.

### 4. Ligar o sensor
- **Físico:** veja [Firmware](#firmware-esp32).
- **Simulado:** `python scripts/simular_sensor.py --falha`

### 5. Ver os outros squads recebendo
```bash
pip install pika
python scripts/consumidor.py finance
python scripts/consumidor.py fleet
```

## Firmware ESP32

| Sensor DHT | ESP32 |
|---|---|
| VCC / + | 3V3 |
| DATA / OUT | GPIO 4 (D4) |
| GND / − | GND |

Os módulos em plaquinha de 3 pinos já têm o resistor de pull-up.

```bash
cp firmware/sensor_esp32/config.example.h firmware/sensor_esp32/config.h   # preencha Wi-Fi, IP do PC e a chave
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/sensor_esp32
arduino-cli upload  --fqbn esp32:esp32:esp32 -p /dev/ttyUSB0 firmware/sensor_esp32
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
```
Com DHT11, troque `DHT_TIPO` para `DHT11` no `config.h`. O ESP32 e o PC precisam estar na mesma rede Wi-Fi.

## Desenvolvimento
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
ruff check src tests scripts
pytest                                   # unit + integration + contract
uvicorn src.api.main:app --reload        # API local sem Docker (RabbitMQ opcional)
python -m scripts.exportar_openapi       # depois de mudar qualquer rota
```

Fluxo de branches e PRs: [`docs/git_strategy.md`](docs/git_strategy.md).

## Estrutura
| Pasta | Conteúdo |
|---|---|
| `src/` | `api/` · `application/` · `domain/` · `infrastructure/` · `config/` |
| `tests/` | `unit/` · `integration/` · `contract/` |
| `contracts/` | OpenAPI e contrato de eventos |
| `docs/` | Documentos 01–13, [ADRs](docs/adr/) e estratégia Git |
| `firmware/` | Código do ESP32 |
| `monitoring/` | Prometheus e dashboard Grafana |
| `scripts/` | Simulador, consumidor de exemplo, K6, instalação |
| `.github/workflows/` | CI (lint, testes, build, Trivy, Sonar, docker) e CD (GHCR) |

## Status
| Entrega | Situação |
|---|---|
| Sensor físico + gateway + eventos | ✅ |
| Testes unit/integration/contract | ✅ 19 testes |
| OpenAPI, catálogo de eventos, ADRs, docs | ✅ (campos ✏️ para o squad completar) |
| Docker, Compose, CI/CD, Prometheus, Grafana | ✅ |
| MongoDB | ⏳ hoje em memória |
| `CargaForaDaRota`, consumo de `CargaExpedida`, UC09 | ⏳ |
| OpenTelemetry + Jaeger, métricas HTTP | ⏳ |
| Resultados do K6 | ⏳ |

## Licença
MIT — veja [LICENSE](LICENSE).
