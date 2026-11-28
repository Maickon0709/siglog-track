# SIG-Log Track — Rastreamento de Cargas & Telemetria IoT (Squad 03)

Módulo da plataforma **SIG-Log** que responde: **"Onde está a carga?"** e **"A carga está dentro das condições adequadas?"**

Um sensor físico (ESP32 + DHT22/DHT11) envia temperatura, umidade, bateria e posição. O Track detecta as anomalias
e publica eventos no RabbitMQ para o **Fleet (Squad 02)**, o **Finance (Squad 04)** e o **CRM (Squad 06)**.

```
ESP32 + DHT22 ──HTTP──► SIG-Log Track ──RabbitMQ (siglog.tracking.events)──► Frota · Financeiro · CRM
WMS ──wms.carga.expedida.v1──► SIG-Log Track (status da carga)
                              └── /metrics ──► Prometheus ──► Grafana
```

## Para os outros squads
Vocês **não precisam do nosso código**, só do contrato e de uma **chave de API** (header `X-API-Key`),
que o Squad 03 entrega para cada squad. Veja [Chaves de API](contracts/CONTRATO_EVENTOS.md#8-chaves-de-api-entre-squads).
- Eventos: [`contracts/CONTRATO_EVENTOS.md`](contracts/CONTRATO_EVENTOS.md) + [`events.schema.json`](contracts/events.schema.json) + [`events.examples.json`](contracts/events.examples.json)
- Filas e DLQs: [`monitoring/rabbitmq/definitions.json`](monitoring/rabbitmq/definitions.json) — mesma convenção do WMS
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
docker compose up --build    # sem o plugin buildx: DOCKER_BUILDKIT=0 docker build -t siglog-track:local . && docker compose up -d --no-build
```
| Serviço | Endereço |
|---|---|
| API + OpenAPI | http://localhost:8000/docs |
| RabbitMQ | http://localhost:15672 (guest/guest) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) → pasta *SIG-Log* |

### 3. Vincular o sensor à carga
```bash
curl -X POST localhost:8000/devices -H 'Content-Type: application/json' -H 'X-API-Key: dev-track' \
  -d '{"deviceId":"IOT-001","shipmentId":"EXP-001","vehicleId":"VEI-042","tripId":"VIA-2026-0917","tipoCarga":"VACINA"}'
```
Faixas padrão: VACINA 2–8 °C · RESFRIADO 0–7 °C / ≤ 90 % · CONGELADO ≤ −18 °C · AMBIENTE 15–30 °C / ≤ 70 %.

### 4. Ligar o sensor
- **Físico:** veja [Firmware](#firmware-esp32).
- **Simulado:** `python scripts/simular_sensor.py --falha`

### 5. Teste de ponta a ponta
Com o `docker compose up` rodando, confere sensor → filas → schema, o `CargaExpedida` do WMS, a DLQ,
o Prometheus e o Grafana (25 verificações):
```bash
python -m scripts.teste_ponta_a_ponta
```

### 6. Ver os outros squads recebendo
```bash
pip install pika
python scripts/consumidor.py financeiro
python scripts/consumidor.py frota
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
| `monitoring/` | Prometheus, dashboard Grafana e definições do RabbitMQ |
| `scripts/` | Simulador, consumidor de exemplo, K6, instalação |
| `.github/workflows/` | CI (lint, testes, build, Trivy, Sonar, docker) e CD (GHCR) |

## Status
| Entrega | Situação |
|---|---|
| Sensor físico + gateway + eventos | ✅ |
| Testes unit/integration/contract | ✅ 54 testes |
| OpenAPI, catálogo de eventos, ADRs, docs | ✅ (campos ✏️ para o squad completar) |
| Docker, Compose, CI/CD, Prometheus, Grafana | ✅ |
| MongoDB | ⏳ hoje em memória |
| Consumo do `CargaExpedida` (WMS) e UC09 status da carga | ✅ |
| `CargaForaDaRota` | ⏳ |
| OpenTelemetry + Jaeger, métricas HTTP | ⏳ |
| Resultados do K6 | ⏳ |

## Licença
MIT — veja [LICENSE](LICENSE).
