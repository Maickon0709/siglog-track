import pytest
from fastapi.testclient import TestClient

from src.api.main import criar_app
from src.application.servico_telemetria import ServicoTelemetria
from src.config import settings
from src.infrastructure.publicador import PublicadorEmMemoria
from src.infrastructure.repositorio import RepositorioEmMemoria

CHAVE = {"X-Device-Key": settings.DEVICE_API_KEY}


@pytest.fixture
def ctx():
    """Cliente HTTP da API com publicador em memoria e um sensor ja vinculado."""
    pub = PublicadorEmMemoria()
    servico = ServicoTelemetria(RepositorioEmMemoria(100), pub, settings.SERVICE_NAME, 60)
    with TestClient(criar_app(servico, iniciar_monitor=False), headers={"X-API-Key": "dev-fleet"}) as client:
        client.post("/devices", json={"deviceId": "IOT-001", "shipmentId": "EXP-001",
                                      "vehicleId": "VEI-042", "tripId": "VIA-1", "tipoCarga": "VACINA"})
        yield client, pub


@pytest.fixture
def enviar():
    def _enviar(client, temp, **extra):
        return client.post("/sensor-readings", headers=CHAVE,
                           json={"deviceId": "IOT-001", "temperatura": temp, **extra})
    return _enviar
