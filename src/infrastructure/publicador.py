"""Publicacao de eventos no RabbitMQ (exchange topic compartilhado da plataforma)."""
from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone

import pika

log = logging.getLogger("siglog-track.publicador")


def envelope(evento: str, dados: dict, source: str) -> dict:
    return {
        "event": evento,
        "eventId": str(uuid.uuid4()),
        "version": 1,
        "source": source,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "correlationId": dados.get("shipmentId"),
        "data": dados,
    }


class PublicadorRabbitMQ:
    """Conexao unica protegida por lock: pika nao e thread-safe."""

    def __init__(self, url: str, exchange: str, prefixo: str):
        self._params = pika.URLParameters(url)
        self._exchange = exchange
        self._prefixo = prefixo
        self._lock = threading.Lock()
        self._conn: pika.BlockingConnection | None = None
        self._canal = None

    def _conectar(self) -> None:
        self._conn = pika.BlockingConnection(self._params)
        self._canal = self._conn.channel()
        self._canal.exchange_declare(self._exchange, exchange_type="topic", durable=True)
        self._canal.confirm_delivery()

    def publicar(self, msg: dict) -> None:
        routing_key = f"{self._prefixo}.{msg['event']}"
        corpo = json.dumps(msg, ensure_ascii=False).encode()
        props = pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            message_id=msg["eventId"],
            type=msg["event"],
            correlation_id=msg.get("correlationId"),
        )
        with self._lock:
            for tentativa in (1, 2):
                try:
                    if self._conn is None or self._conn.is_closed:
                        self._conectar()
                    self._canal.basic_publish(self._exchange, routing_key, corpo, props)
                    return
                except pika.exceptions.AMQPError:
                    self._conn = None
                    if tentativa == 2:
                        raise
                    log.warning("RabbitMQ indisponivel, reconectando")

    def fechar(self) -> None:
        with self._lock:
            if self._conn and self._conn.is_open:
                self._conn.close()


class PublicadorEmMemoria:
    """Usado nos testes: guarda as mensagens em vez de enviar."""

    def __init__(self):
        self.mensagens: list[dict] = []

    def publicar(self, msg: dict) -> None:
        self.mensagens.append(msg)

    def fechar(self) -> None:
        pass
