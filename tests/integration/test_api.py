"""Integracao: API -> servico -> repositorio -> publicador."""
from tests.conftest import CHAVE


def test_chave_invalida(ctx):
    client, _ = ctx
    r = client.post("/sensor-readings", headers={"X-Device-Key": "errada"},
                    json={"deviceId": "IOT-001", "temperatura": 5})
    assert r.status_code == 401


def test_dispositivo_nao_registrado(ctx):
    client, _ = ctx
    r = client.post("/sensor-readings", headers=CHAVE, json={"deviceId": "X", "temperatura": 5})
    assert r.status_code == 404


def test_leitura_invalida(ctx, enviar):
    client, _ = ctx
    assert enviar(client, 500).status_code == 422


def test_fluxo_completo(ctx, enviar):
    client, pub = ctx
    for t in (9.0, 9.5, 10.5):
        assert enviar(client, t, umidade=60, bateria=80, latitude=-23.55, longitude=-46.63).status_code == 202
    enviar(client, 5.0)

    eventos = [m["event"] for m in pub.mensagens]
    assert "AlertaTemperatura" in eventos and "AlertaTemperaturaEncerrado" in eventos
    alertas = client.get("/alerts", params={"shipmentId": "EXP-001"}).json()
    assert alertas[0]["status"] == "ENCERRADO"
    assert client.get("/shipments/EXP-001/location").json()["latitude"] == -23.55
    assert len(client.get("/shipments/EXP-001/history").json()) == 4
    assert client.get("/devices/IOT-001").json()["online"] is True


def test_metricas_expostas(ctx, enviar):
    client, _ = ctx
    enviar(client, 5.0)
    assert "track_temperatura_celsius" in client.get("/metrics").text
