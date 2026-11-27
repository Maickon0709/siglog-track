"""Chave de API por squad (X-API-Key) e permissao de vincular sensores."""
import pytest

from src.config.settings import _ler_chaves

DISPOSITIVO = {"deviceId": "IOT-009", "shipmentId": "EXP-009", "tipoCarga": "VACINA"}


@pytest.mark.parametrize("rota", ["/alerts", "/devices/IOT-001", "/shipments/EXP-001/history"])
def test_consulta_sem_chave_401(ctx, rota):
    client, _ = ctx
    assert client.get(rota, headers={"X-API-Key": ""}).status_code == 401


def test_chave_errada_401(ctx):
    client, _ = ctx
    assert client.get("/alerts", headers={"X-API-Key": "chave-falsa"}).status_code == 401


@pytest.mark.parametrize("chave", ["dev-finance", "dev-crm", "dev-wms", "dev-people"])
def test_todos_os_squads_consultam(ctx, chave):
    client, _ = ctx
    assert client.get("/alerts", headers={"X-API-Key": chave}).status_code == 200


@pytest.mark.parametrize("chave,status", [
    ("dev-fleet", 201), ("dev-wms", 201), ("dev-track", 201),
    ("dev-finance", 403), ("dev-crm", 403), ("dev-people", 403),
])
def test_quem_pode_vincular_sensor(ctx, chave, status):
    client, _ = ctx
    assert client.post("/devices", json=DISPOSITIVO, headers={"X-API-Key": chave}).status_code == status


def test_sensor_nao_usa_chave_de_squad(ctx):
    """O ESP32 continua usando X-Device-Key; chave de squad nao serve para enviar leitura."""
    client, _ = ctx
    r = client.post("/sensor-readings", headers={"X-Device-Key": "dev-fleet"},
                    json={"deviceId": "IOT-001", "temperatura": 5})
    assert r.status_code == 401


def test_health_e_metrics_sao_publicos(ctx):
    client, _ = ctx
    assert client.get("/health", headers={"X-API-Key": ""}).status_code == 200
    assert client.get("/metrics", headers={"X-API-Key": ""}).status_code == 200


def test_ler_chaves_do_ambiente():
    assert _ler_chaves(" fleet=abc , Finance=def,,quebrado ") == {"abc": "fleet", "def": "finance"}
