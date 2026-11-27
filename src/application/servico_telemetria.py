"""Casos de uso: UC01 registrar dispositivo, UC02-04 receber leituras,
UC05-06 consultas, UC07-08 detectar condicao critica e gerar alerta."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from src.domain.monitoramento import (
    FAIXAS_POR_TIPO,
    Dispositivo,
    Faixa,
    Leitura,
    processar_leitura,
    verificar_offline,
)
from src.infrastructure import metricas
from src.infrastructure.publicador import envelope

log = logging.getLogger("siglog-track")

TOLERANCIA_RELOGIO = timedelta(minutes=5)


class DispositivoNaoEncontrado(Exception):
    pass


class ServicoTelemetria:
    def __init__(self, repo, publicador, source: str, offline_segundos: int):
        self.repo = repo
        self.publicador = publicador
        self.source = source
        self.offline_segundos = offline_segundos

    def _publicar(self, nome: str, dados: dict) -> None:
        msg = envelope(nome, dados, self.source)
        try:
            self.publicador.publicar(msg)
            metricas.eventos_publicados_total.labels(nome).inc()
        except Exception:
            # A leitura nao e perdida (ja esta no historico); so o evento falhou.
            metricas.erros_publicacao_total.inc()
            log.exception("falha ao publicar", extra={"evento": nome, "eventId": msg["eventId"]})
            return
        if nome != "TemperaturaAtualizada":
            log.info(nome, extra={"evento": nome, "eventId": msg["eventId"],
                                  "shipmentId": dados.get("shipmentId")})

    def registrar_dispositivo(self, device_id: str, shipment_id: str, tipo_carga: str,
                              vehicle_id: str | None = None, trip_id: str | None = None,
                              temp_min: float | None = None, temp_max: float | None = None,
                              umidade_max: float | None = None) -> Dispositivo:
        padrao = FAIXAS_POR_TIPO.get(tipo_carga.upper(), Faixa(None, None))
        faixa = Faixa(
            temp_min if temp_min is not None else padrao.temp_min,
            temp_max if temp_max is not None else padrao.temp_max,
            umidade_max if umidade_max is not None else padrao.umidade_max,
        )
        disp = Dispositivo(device_id=device_id, shipment_id=shipment_id, tipo_carga=tipo_carga.upper(),
                           faixa=faixa, vehicle_id=vehicle_id, trip_id=trip_id)
        with self.repo.lock:
            anterior = self.repo.dispositivo(device_id)
            if anterior and anterior.shipment_id == shipment_id:
                # Re-vinculo da mesma carga (ex.: troca de veiculo): mantem o estado dos alertas.
                disp.ativas, disp.fora_seguidas = anterior.ativas, anterior.fora_seguidas
                disp.primeira_fora, disp.extremo_fora = anterior.primeira_fora, anterior.extremo_fora
                disp.ultima_leitura = anterior.ultima_leitura
                disp.ultima_recepcao = anterior.ultima_recepcao
            self.repo.salvar_dispositivo(disp)
        log.info("DispositivoRegistrado", extra={"evento": "DispositivoRegistrado", "shipmentId": shipment_id})
        return disp

    def receber_leitura(self, device_id: str, temperatura: float, umidade: float | None,
                        bateria: int | None, latitude: float | None, longitude: float | None,
                        timestamp: datetime | None) -> list[str]:
        agora = datetime.now(timezone.utc)
        # Relogio do sensor ausente ou muito diferente do servidor -> usa a hora do servidor.
        if timestamp is None or abs(timestamp - agora) > TOLERANCIA_RELOGIO:
            timestamp = agora
        leitura = Leitura(temperatura, timestamp, umidade, bateria, latitude, longitude)

        with self.repo.lock:
            disp = self.repo.dispositivo(device_id)
            if disp is None:
                raise DispositivoNaoEncontrado(device_id)
            eventos = processar_leitura(disp, leitura, agora)
            self.repo.registrar_leitura(disp.shipment_id, {
                "deviceId": device_id, "timestamp": timestamp.isoformat().replace("+00:00", "Z"),
                "temperatura": temperatura, "umidade": umidade, "bateria": bateria,
                "latitude": latitude, "longitude": longitude,
            })
            for nome, dados in eventos:
                if nome == "AlertaTemperatura":
                    self.repo.registrar_alerta({**dados, "status": "ATIVO"})
                elif nome == "AlertaTemperaturaEncerrado":
                    self.repo.encerrar_alerta(dados["alertId"], dados)
            alertas_ativos = sum(len(d.ativas) for d in self.repo.dispositivos())

        metricas.leituras_total.labels(device_id).inc()
        metricas.temperatura.labels(device_id, disp.shipment_id).set(temperatura)
        if umidade is not None:
            metricas.umidade.labels(device_id, disp.shipment_id).set(umidade)
        metricas.alertas_ativos.set(alertas_ativos)

        for nome, dados in eventos:
            self._publicar(nome, dados)
        return [nome for nome, _ in eventos]

    def verificar_offline(self) -> None:
        agora = datetime.now(timezone.utc)
        with self.repo.lock:
            dispositivos = self.repo.dispositivos()
            eventos = [e for d in dispositivos if (e := verificar_offline(d, agora, self.offline_segundos))]
            online = sum(1 for d in dispositivos if d.ultima_recepcao and not d.offline_notificado)
        metricas.dispositivos_online.set(online)
        for nome, dados in eventos:
            self._publicar(nome, dados)

    def localizacao(self, shipment_id: str) -> dict | None:
        with self.repo.lock:
            for leitura in reversed(self.repo.historico(shipment_id, 10_000)):
                if leitura["latitude"] is not None:
                    return {"shipmentId": shipment_id, **leitura}
        return None

    def historico(self, shipment_id: str, limite: int) -> list[dict]:
        with self.repo.lock:
            return self.repo.historico(shipment_id, limite)

    def alertas(self, shipment_id: str | None) -> list[dict]:
        with self.repo.lock:
            return [dict(a) for a in self.repo.alertas(shipment_id)]
