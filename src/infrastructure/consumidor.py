"""Consumo dos eventos de outros modulos (hoje: fila tracking.wms.events, publicada pelo WMS).

A fila tem DLQ: mensagem que nao e JSON ou que quebra o processamento recebe nack sem requeue
e vai para tracking.wms.events.dlq, sem travar as demais.
"""
from __future__ import annotations

import json
import logging
import threading
from collections.abc import Callable

import pika

log = logging.getLogger("siglog-track.consumidor")


def tratar_mensagem(corpo: bytes, processar: Callable[[dict], bool]) -> bool:
    """Decodifica e processa. Devolve True para ack e False para mandar a mensagem para a DLQ."""
    try:
        msg = json.loads(corpo)
        if not isinstance(msg, dict):
            raise ValueError("mensagem nao e um objeto JSON")
        processar(msg)
        return True
    except Exception:
        log.exception("mensagem rejeitada para a DLQ", extra={"evento": "MensagemRejeitada"})
        return False


class ConsumidorRabbitMQ:
    def __init__(self, url: str, fila: str, processar: Callable[[dict], bool]):
        self._params = pika.URLParameters(url)
        self._fila = fila
        self._processar = processar
        self._parar = threading.Event()
        self._conn: pika.BlockingConnection | None = None

    def _callback(self, canal, metodo, _props, corpo):
        if tratar_mensagem(corpo, self._processar):
            canal.basic_ack(metodo.delivery_tag)
        else:
            canal.basic_nack(metodo.delivery_tag, requeue=False)

    def _rodar(self) -> None:
        while not self._parar.is_set():
            try:
                self._conn = pika.BlockingConnection(self._params)
                canal = self._conn.channel()
                canal.queue_declare(self._fila, passive=True)  # a fila vem das definicoes do RabbitMQ
                canal.basic_qos(prefetch_count=20)
                canal.basic_consume(self._fila, self._callback)
                log.info("consumindo", extra={"evento": f"Consumindo {self._fila}"})
                while not self._parar.is_set():
                    self._conn.process_data_events(time_limit=1)
            except pika.exceptions.AMQPError:
                log.warning("sem conexao com a fila, tentando de novo em 5 s",
                            extra={"evento": f"FilaIndisponivel {self._fila}"})
                self._parar.wait(5)
            finally:
                if self._conn and self._conn.is_open:
                    self._conn.close()

    def iniciar(self) -> None:
        threading.Thread(target=self._rodar, daemon=True, name=f"consumidor-{self._fila}").start()

    def parar(self) -> None:
        self._parar.set()
