"""Publicacao de eventos no RabbitMQ, na convencao da plataforma (a mesma do WMS):

- exchange topic do modulo: siglog.tracking.events
- routing key: tracking.<evento.em.pontos>.v<versao>  (ex.: tracking.alerta.temperatura.v1)
- mensagem com os campos na raiz: event, version, eventId, timestamp, correlationId, source + dados
"""
from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone

import pika

log = logging.getLogger("siglog-track.publicador")

VERSAO = 1


def routing_key(prefixo: str, evento: str, versao: int = VERSAO) -> str:
    """("tracking", "AlertaTemperaturaEncerrado") -> "tracking.alerta.temperatura.encerrado.v1"."""
    pontos = re.sub(r"(?<!^)(?=[A-Z])", ".", evento).lower()
    return f"{prefixo}.{pontos}.v{versao}"


def envelope(evento: str, dados: dict, source: str) -> dict:
    return {
        "event": evento,
        "version": VERSAO,
        "eventId": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "correlationId": dados["shipmentId"],
        "source": source,
        **dados,
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
        chave = routing_key(self._prefixo, msg["event"], msg["version"])
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
                    self._canal.basic_publish(self._exchange, chave, corpo, props)
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

    def __init__(self, prefixo: str = "tracking"):
        self.prefixo = prefixo
        self.mensagens: list[dict] = []
        self.routing_keys: list[str] = []

    def publicar(self, msg: dict) -> None:
        self.mensagens.append(msg)
        self.routing_keys.append(routing_key(self.prefixo, msg["event"], msg["version"]))

    def fechar(self) -> None:
        pass
