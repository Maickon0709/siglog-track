"""Convencao de mensageria da plataforma (igual a do WMS)."""
import pytest

from src.domain.carga import EM_TRANSITO, EventoInvalido, aplicar_carga_expedida
from src.infrastructure.consumidor import tratar_mensagem
from src.infrastructure.publicador import envelope, routing_key


@pytest.mark.parametrize("evento,chave", [
    ("TemperaturaAtualizada", "tracking.temperatura.atualizada.v1"),
    ("PosicaoAtualizada", "tracking.posicao.atualizada.v1"),
    ("AlertaTemperatura", "tracking.alerta.temperatura.v1"),
    ("AlertaTemperaturaEncerrado", "tracking.alerta.temperatura.encerrado.v1"),
    ("DispositivoOffline", "tracking.dispositivo.offline.v1"),
])
def test_routing_key(evento, chave):
    assert routing_key("tracking", evento) == chave


def test_routing_key_igual_a_do_wms():
    assert routing_key("wms", "CargaExpedida") == "wms.carga.expedida.v1"


def test_envelope_campos_na_raiz():
    msg = envelope("DispositivoOffline", {"shipmentId": "EXP-1", "deviceId": "IOT-1"}, "tracking")
    assert msg["source"] == "tracking" and msg["correlationId"] == "EXP-1"
    assert msg["deviceId"] == "IOT-1" and "data" not in msg
    assert msg["timestamp"].endswith("Z") and "." not in msg["timestamp"]


def test_carga_expedida_vira_em_transito():
    carga = aplicar_carga_expedida(None, {"shipmentId": "EXP-1", "timestamp": "2026-11-26T14:00:00Z",
                                          "orderIds": ["PED-1"], "destination": "Recife - PE"})
    assert carga.status == EM_TRANSITO and carga.pedidos == ["PED-1"]


def test_carga_expedida_sem_shipment_e_invalida():
    with pytest.raises(EventoInvalido):
        aplicar_carga_expedida(None, {"timestamp": "2026-11-26T14:00:00Z"})


def test_mensagem_quebrada_vai_para_dlq():
    assert tratar_mensagem(b"nao e json", lambda m: True) is False
    assert tratar_mensagem(b"[1, 2]", lambda m: True) is False


def test_erro_no_processamento_vai_para_dlq():
    def explode(_):
        raise RuntimeError("falhou")
    assert tratar_mensagem(b'{"event": "X"}', explode) is False


def test_mensagem_ok_recebe_ack():
    assert tratar_mensagem(b'{"event": "X"}', lambda m: False) is True
