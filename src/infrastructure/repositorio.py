"""Repositorio em memoria.

Para o projeto final, troque por uma implementacao MongoDB com os mesmos
metodos (colecoes: dispositivos, leituras, alertas).
"""
from __future__ import annotations

import threading
from collections import defaultdict, deque

from src.domain.monitoramento import Dispositivo


class RepositorioEmMemoria:
    def __init__(self, historico_max: int):
        self.lock = threading.RLock()
        self._dispositivos: dict[str, Dispositivo] = {}
        self._historico: dict[str, deque] = defaultdict(lambda: deque(maxlen=historico_max))
        self._alertas: list[dict] = []

    def salvar_dispositivo(self, disp: Dispositivo) -> None:
        self._dispositivos[disp.device_id] = disp

    def dispositivo(self, device_id: str) -> Dispositivo | None:
        return self._dispositivos.get(device_id)

    def dispositivos(self) -> list[Dispositivo]:
        return list(self._dispositivos.values())

    def registrar_leitura(self, shipment_id: str, registro: dict) -> None:
        self._historico[shipment_id].append(registro)

    def historico(self, shipment_id: str, limite: int) -> list[dict]:
        return list(self._historico.get(shipment_id, ()))[-limite:]

    def registrar_alerta(self, alerta: dict) -> None:
        self._alertas.append(alerta)

    def encerrar_alerta(self, alert_id: str, dados: dict) -> None:
        for a in self._alertas:
            if a["alertId"] == alert_id:
                a.update(status="ENCERRADO", fimViolacao=dados["fimViolacao"],
                         duracaoSegundos=dados["duracaoSegundos"], valorExtremo=dados["valorExtremo"])

    def alertas(self, shipment_id: str | None = None) -> list[dict]:
        return [a for a in self._alertas if shipment_id is None or a["shipmentId"] == shipment_id]
