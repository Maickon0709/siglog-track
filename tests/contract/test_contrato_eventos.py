"""Contrato: toda mensagem publicada para Fleet/Finance/CRM segue contracts/events.schema.json."""
import json
from pathlib import Path

import jsonschema
import pytest

SCHEMA = json.loads((Path(__file__).parents[2] / "contracts" / "events.schema.json").read_text())


def test_eventos_publicados_respeitam_schema(ctx, enviar):
    client, pub = ctx
    for t in (9.0, 9.5, 10.5, 5.0):
        enviar(client, t, umidade=60, bateria=80, latitude=-23.55, longitude=-46.63)
    assert {m["event"] for m in pub.mensagens} >= {
        "TemperaturaAtualizada", "PosicaoAtualizada", "AlertaTemperatura", "AlertaTemperaturaEncerrado",
    }
    for msg in pub.mensagens:
        jsonschema.validate(msg, SCHEMA)
        assert msg["correlationId"] == "EXP-001"
    assert "tracking.alerta.temperatura.v1" in pub.routing_keys


def test_contrato_offline(ctx, enviar):
    client, pub = ctx
    enviar(client, 5.0)
    servico = client.app.state.servico
    servico.offline_segundos = -1
    servico.verificar_offline()
    assert pub.mensagens[-1]["event"] == "DispositivoOffline"
    jsonschema.validate(pub.mensagens[-1], SCHEMA)


def test_exemplos_publicados_seguem_o_schema():
    exemplos = json.loads((Path(__file__).parents[2] / "contracts" / "events.examples.json").read_text())
    assert set(exemplos) == set(SCHEMA["$defs"])
    for msg in exemplos.values():
        jsonschema.validate(msg, SCHEMA)


def test_schema_rejeita_payload_quebrado():
    msg = {"event": "AlertaTemperatura", "eventId": "x", "version": 1, "source": "tracking",
           "timestamp": "2026-11-26T14:00:00Z", "correlationId": "EXP-001", "deviceId": "IOT-001"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(msg, SCHEMA)


def test_openapi_publicado_esta_atualizado():
    """O contracts/openapi.yaml precisa bater com a API real (rode scripts/exportar_openapi.py)."""
    yaml = pytest.importorskip("yaml")
    from src.api.main import criar_app
    publicado = yaml.safe_load((Path(__file__).parents[2] / "contracts" / "openapi.yaml").read_text())
    assert publicado["paths"].keys() == criar_app(iniciar_monitor=False).openapi()["paths"].keys()
