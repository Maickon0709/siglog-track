"""API REST do SIG-Log Track (sensor). OpenAPI em /docs e /openapi.json."""
from __future__ import annotations

import hmac
import json
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from src.api.seguranca import exigir_squad, squad_autenticado
from src.application.servico_telemetria import DispositivoNaoEncontrado, ServicoTelemetria
from src.config import settings
from src.infrastructure.publicador import PublicadorRabbitMQ
from src.infrastructure.repositorio import RepositorioEmMemoria


class LogJson(logging.Formatter):
    """Log estruturado no formato do kit: timestamp, service, event, level."""

    def format(self, record):
        dados = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "service": settings.SERVICE_NAME,
            "event": getattr(record, "evento", record.getMessage()),
            "level": record.levelname,
        }
        for campo in ("eventId", "shipmentId"):
            if hasattr(record, campo):
                dados[campo] = getattr(record, campo)
        if record.exc_info:
            dados["erro"] = self.formatException(record.exc_info)
        return json.dumps(dados, ensure_ascii=False)


_handler = logging.StreamHandler()
_handler.setFormatter(LogJson())
logging.getLogger("siglog-track").handlers = [_handler]
logging.getLogger("siglog-track").setLevel(logging.INFO)
logging.getLogger("siglog-track").propagate = False


class DispositivoIn(BaseModel):
    deviceId: str = Field(examples=["IOT-001"])
    shipmentId: str = Field(examples=["EXP-001"], description="Vem do WMS (CargaExpedida)")
    vehicleId: str | None = Field(None, examples=["VEI-042"], description="Vem do Fleet")
    tripId: str | None = Field(None, examples=["VIA-2026-0917"], description="Vem do Fleet")
    tipoCarga: str = Field("VACINA", description="VACINA, RESFRIADO, CONGELADO, AMBIENTE ou outro")
    tempMin: float | None = None
    tempMax: float | None = None
    umidadeMax: float | None = None


class LeituraIn(BaseModel):
    deviceId: str
    temperatura: float = Field(ge=-60, le=100)
    umidade: float | None = Field(None, ge=0, le=100)
    bateria: int | None = Field(None, ge=0, le=100)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    timestamp: datetime | None = None


def criar_app(servico: ServicoTelemetria | None = None, iniciar_monitor: bool = True) -> FastAPI:
    if servico is None:
        servico = ServicoTelemetria(
            RepositorioEmMemoria(settings.HISTORICO_MAX_POR_CARGA),
            PublicadorRabbitMQ(settings.RABBITMQ_URL, settings.EXCHANGE, settings.ROUTING_PREFIX),
            settings.SERVICE_NAME,
            settings.OFFLINE_SEGUNDOS,
        )

    @asynccontextmanager
    async def ciclo_de_vida(_app):
        parar = threading.Event()

        def monitor():
            while not parar.wait(10):
                servico.verificar_offline()

        if iniciar_monitor:
            threading.Thread(target=monitor, daemon=True, name="monitor-offline").start()
        yield
        parar.set()
        servico.publicador.fechar()

    app = FastAPI(
        title="SIG-Log Track — Sensor IoT",
        version="1.1.0",
        description="Consultas e cadastro exigem o header **X-API-Key** do seu squad. "
                    "O sensor usa **X-Device-Key** em `/sensor-readings`.",
        lifespan=ciclo_de_vida,
    )
    vincula = Depends(exigir_squad(settings.SQUADS_QUE_VINCULAM_DISPOSITIVOS))
    consulta = Depends(squad_autenticado)
    app.state.servico = servico

    def _disp_out(d):
        return {
            "deviceId": d.device_id, "shipmentId": d.shipment_id, "vehicleId": d.vehicle_id,
            "tripId": d.trip_id, "tipoCarga": d.tipo_carga,
            "faixa": {"tempMin": d.faixa.temp_min, "tempMax": d.faixa.temp_max,
                      "umidadeMax": d.faixa.umidade_max},
            "ultimaLeitura": d.ultima_leitura.isoformat().replace("+00:00", "Z") if d.ultima_leitura else None,
            "online": bool(d.ultima_recepcao) and not d.offline_notificado,
            "alertasAtivos": list(d.ativas),
        }

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/devices", status_code=201, tags=["dispositivos"], dependencies=[vincula])
    def registrar_dispositivo(body: DispositivoIn):
        d = servico.registrar_dispositivo(
            body.deviceId, body.shipmentId, body.tipoCarga, body.vehicleId, body.tripId,
            body.tempMin, body.tempMax, body.umidadeMax,
        )
        return _disp_out(d)

    @app.get("/devices/{device_id}", tags=["dispositivos"], dependencies=[consulta])
    def obter_dispositivo(device_id: str):
        d = servico.repo.dispositivo(device_id)
        if d is None:
            raise HTTPException(404, "dispositivo nao registrado")
        return _disp_out(d)

    @app.post("/sensor-readings", status_code=202, tags=["telemetria"])
    def receber_leitura(body: LeituraIn, x_device_key: str = Header(default="")):
        if not hmac.compare_digest(x_device_key, settings.DEVICE_API_KEY):
            raise HTTPException(401, "X-Device-Key invalida")
        ts = body.timestamp
        if ts is not None and ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        try:
            eventos = servico.receber_leitura(body.deviceId, body.temperatura, body.umidade, body.bateria,
                                              body.latitude, body.longitude, ts)
        except DispositivoNaoEncontrado:
            raise HTTPException(404, "dispositivo nao registrado: faca POST /devices primeiro") from None
        return {"eventos": eventos}

    @app.get("/shipments/{shipment_id}/location", tags=["consultas"], dependencies=[consulta])
    def localizacao(shipment_id: str):
        loc = servico.localizacao(shipment_id)
        if loc is None:
            raise HTTPException(404, "sem posicao para esta carga")
        return loc

    @app.get("/shipments/{shipment_id}/history", tags=["consultas"], dependencies=[consulta])
    def historico(shipment_id: str, limit: int = Query(100, ge=1, le=5000)):
        return servico.historico(shipment_id, limit)

    @app.get("/alerts", tags=["consultas"], dependencies=[consulta])
    def alertas(shipmentId: str | None = None):
        return servico.alertas(shipmentId)

    return app


app = criar_app()
