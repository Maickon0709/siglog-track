"""Teste de ponta a ponta com o `docker compose up` rodando (Track + RabbitMQ + Prometheus + Grafana).

Simula o sensor, confere as mensagens nas filas da Frota/Financeiro/CRM contra o schema,
publica um CargaExpedida como o WMS publica e verifica a DLQ, o Prometheus e o Grafana.

Uso:
    python -m scripts.teste_ponta_a_ponta
So usa a biblioteca padrao + jsonschema (requirements-dev.txt).
"""
import base64
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import jsonschema

TRACK = "http://localhost:8000"
RABBIT = "http://localhost:15672/api"
PROMETHEUS = "http://localhost:9090/api/v1"
GRAFANA = "http://localhost:3000/api"
SCHEMA = json.loads((Path(__file__).parents[1] / "contracts" / "events.schema.json").read_text())
CHAVE_SQUAD = {"X-API-Key": "dev-track"}
CHAVE_SENSOR = {"X-Device-Key": "troque-esta-chave"}
GUEST = {"Authorization": "Basic " + base64.b64encode(b"guest:guest").decode()}
SHIPMENT = f"EXP-E2E-{uuid.uuid4().hex[:6]}"
DEVICE = f"IOT-E2E-{uuid.uuid4().hex[:6]}"

falhas = 0


def http(metodo, url, corpo=None, headers=None):
    dados = json.dumps(corpo).encode() if corpo is not None else None
    req = urllib.request.Request(url, dados, {"Content-Type": "application/json", **(headers or {})}, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            texto = r.read().decode()
            return r.status, json.loads(texto) if texto else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def ok(condicao, descricao):
    global falhas
    print(("  ✅ " if condicao else "  ❌ ") + descricao)
    falhas += not condicao


def esperar(descricao, funcao, segundos=60):
    fim = time.time() + segundos
    while time.time() < fim:
        try:
            if funcao():
                return True
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        time.sleep(1)
    print(f"  ❌ timeout esperando {descricao}")
    return False


def ler_fila(fila, quantidade=50):
    """Le as mensagens da fila (consome com ack, para o teste poder rodar de novo)."""
    _, msgs = http("POST", f"{RABBIT}/queues/%2F/{fila}/get",
                   {"count": quantidade, "ackmode": "ack_requeue_false", "encoding": "auto"}, GUEST)
    return [json.loads(m["payload"]) for m in msgs]


def publicar(exchange, routing_key, payload):
    corpo = {"properties": {"content_type": "application/json", "delivery_mode": 2},
             "routing_key": routing_key, "payload": payload, "payload_encoding": "string"}
    return http("POST", f"{RABBIT}/exchanges/%2F/{exchange}/publish", corpo, GUEST)[1]


def main():
    print("1) Servicos no ar")
    ok(esperar("Track", lambda: http("GET", f"{TRACK}/health")[0] == 200), "Track responde /health")
    ok(esperar("RabbitMQ", lambda: http("GET", f"{RABBIT}/overview", headers=GUEST)[0] == 200), "RabbitMQ no ar")
    _, filas = http("GET", f"{RABBIT}/queues/%2F", headers=GUEST)
    nomes = {q["name"] for q in filas}
    for f in ("frota.tracking.events", "financeiro.tracking.events", "crm.tracking.events", "tracking.wms.events"):
        ok(f in nomes and f + ".dlq" in nomes, f"fila {f} e sua DLQ existem")
    for f in ("frota.tracking.events", "financeiro.tracking.events", "crm.tracking.events"):
        ler_fila(f, 500)  # limpa sobras de execucoes anteriores

    print("2) Sensor -> Track -> filas")
    status, _ = http("POST", f"{TRACK}/devices", {"deviceId": DEVICE, "shipmentId": SHIPMENT,
                                                  "vehicleId": "VEI-042", "tripId": "VIA-E2E", "tipoCarga": "VACINA"},
                     CHAVE_SQUAD)
    ok(status == 201, "sensor vinculado a carga (POST /devices)")
    for temp in (9.0, 9.5, 10.5, 5.0):  # 3 fora da faixa (alerta) e 1 normal (encerra)
        status, _ = http("POST", f"{TRACK}/sensor-readings", {"deviceId": DEVICE, "temperatura": temp, "umidade": 60,
                                                              "bateria": 90, "latitude": -8.05, "longitude": -34.9},
                         CHAVE_SENSOR)
        ok(status == 202, f"leitura {temp} °C aceita")
    time.sleep(2)

    esperado = {
        "frota.tracking.events": {"PosicaoAtualizada": 4, "AlertaTemperatura": 1},
        "financeiro.tracking.events": {"AlertaTemperatura": 1, "AlertaTemperaturaEncerrado": 1},
        "crm.tracking.events": {"PosicaoAtualizada": 4, "AlertaTemperatura": 1, "AlertaTemperaturaEncerrado": 1},
    }
    for fila, contagem in esperado.items():
        msgs = [m for m in ler_fila(fila) if m.get("shipmentId") == SHIPMENT]
        recebidos = {}
        for m in msgs:
            recebidos[m["event"]] = recebidos.get(m["event"], 0) + 1
        ok(recebidos == contagem, f"{fila}: {recebidos}")
        try:
            for m in msgs:
                jsonschema.validate(m, SCHEMA)
            ok(bool(msgs), f"{fila}: todas as mensagens seguem o events.schema.json")
        except jsonschema.ValidationError as erro:
            ok(False, f"{fila}: mensagem fora do schema: {erro.message}")
    _, alertas = http("GET", f"{TRACK}/alerts?shipmentId={SHIPMENT}", headers=CHAVE_SQUAD)
    ok(len(alertas) == 1 and alertas[0]["status"] == "ENCERRADO", "alerta registrado e encerrado em /alerts")

    print("3) WMS -> Track (CargaExpedida)")
    carga = {"event": "CargaExpedida", "version": 1, "eventId": str(uuid.uuid4()),
             "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "correlationId": "PED-E2E",
             "source": "wms", "shipmentId": SHIPMENT, "orderIds": ["PED-E2E"], "destination": "Recife - PE"}
    ok(publicar("siglog.wms.events", "wms.carga.expedida.v1", json.dumps(carga)).get("routed"),
       "CargaExpedida roteado para tracking.wms.events")
    ok(esperar("status da carga", lambda: (http("GET", f"{TRACK}/shipments/{SHIPMENT}", headers=CHAVE_SQUAD)[1]
                                         or {}).get("status") == "EM_TRANSITO", 15),
       f"GET /shipments/{SHIPMENT} -> EM_TRANSITO")

    print("4) Mensagem quebrada vai para a DLQ")
    antes = http("GET", f"{RABBIT}/queues/%2F/tracking.wms.events.dlq", headers=GUEST)[1]["messages"]
    publicar("siglog.wms.events", "wms.carga.expedida.v1", "isto nao e json")
    ok(esperar("DLQ", lambda: http("GET", f"{RABBIT}/queues/%2F/tracking.wms.events.dlq",
                                   headers=GUEST)[1]["messages"] > antes, 15),
       "tracking.wms.events.dlq recebeu a mensagem invalida")

    print("5) Observabilidade")
    ok(esperar("Prometheus", lambda: http("GET", f"{PROMETHEUS}/query?query=up%7Bjob%3D%22siglog-track%22%7D")[1]
               ["data"]["result"][0]["value"][1] == "1", 30), "Prometheus coleta o Track (up=1)")
    ok(esperar("metrica", lambda: http("GET", f"{PROMETHEUS}/query?query=track_eventos_consumidos_total")[1]
               ["data"]["result"], 30), "metrica track_eventos_consumidos_total chegou no Prometheus")
    ok(esperar("Grafana", lambda: http("GET", f"{GRAFANA}/dashboards/uid/siglog-track")[0] == 200, 30),
       "dashboard 'SIG-Log Track — Telemetria' carregado no Grafana")

    print(f"\n{'TUDO OK' if not falhas else f'{falhas} FALHA(S)'}")
    sys.exit(1 if falhas else 0)


if __name__ == "__main__":
    main()
