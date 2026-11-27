"""UC09: o Track consome o CargaExpedida do WMS (fila tracking.wms.events)."""
import json
from pathlib import Path

CARGA_EXPEDIDA = {  # exemplo do contrato publicado pelo WMS (events.examples.json deles)
    "event": "CargaExpedida", "version": 1, "eventId": "7d1f9b3e-2c64-4a1d-9f10-5b0c3a8e4d21",
    "timestamp": "2026-10-12T14:30:00Z", "correlationId": "PED-100", "source": "wms",
    "shipmentId": "EXP-001", "orderIds": ["PED-100"], "destination": "Recife - PE",
}


def test_status_da_carga_antes_e_depois_da_expedicao(ctx):
    client, _ = ctx
    assert client.get("/shipments/EXP-001").status_code == 404
    assert client.app.state.servico.processar_evento_externo(CARGA_EXPEDIDA) is True
    carga = client.get("/shipments/EXP-001").json()
    assert carga["status"] == "EM_TRANSITO"
    assert carga["destination"] == "Recife - PE" and carga["orderIds"] == ["PED-100"]


def test_evento_repetido_e_ignorado(ctx):
    client, _ = ctx
    servico = client.app.state.servico
    assert servico.processar_evento_externo(CARGA_EXPEDIDA) is True
    assert servico.processar_evento_externo(CARGA_EXPEDIDA) is False


def test_outros_eventos_do_wms_sao_ignorados(ctx):
    client, _ = ctx
    msg = {**CARGA_EXPEDIDA, "event": "MercadoriaRecebida", "eventId": "outro"}
    assert client.app.state.servico.processar_evento_externo(msg) is False


def test_status_exige_chave_de_squad(ctx):
    client, _ = ctx
    assert client.get("/shipments/EXP-001", headers={"X-API-Key": ""}).status_code == 401


def test_fila_do_track_nas_definicoes_do_rabbitmq():
    defs = json.loads((Path(__file__).parents[2] / "monitoring/rabbitmq/definitions.json").read_text())
    binds = {(b["source"], b["destination"], b["routing_key"]) for b in defs["bindings"]}
    assert ("siglog.wms.events", "tracking.wms.events", "wms.carga.expedida.v1") in binds
