"""Exemplo de consumidor dos eventos do Track, para a Frota e o Financeiro.

Convencao da plataforma (a mesma do WMS):
  exchange  siglog.tracking.events (topic)
  routing   tracking.<evento.em.pontos>.v1   ex.: tracking.alerta.temperatura.v1
  fila      <consumidor>.tracking.events       ex.: financeiro.tracking.events (+ .dlq)

As filas ja sao criadas pelo monitoring/rabbitmq/definitions.json do Track. Copie este arquivo para o
projeto de voces e troque o corpo de `tratar()`. Em outra linguagem a ideia e a mesma: consumir a fila,
dar ack depois de processar e nack (sem requeue) para mandar mensagens com erro para a DLQ.

Uso:
    pip install pika
    python scripts/consumidor.py frota
    python scripts/consumidor.py financeiro
"""
import json
import os
import sys

import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")

processados: set[str] = set()  # no projeto real: tabela no banco do modulo


def tratar(modulo: str, msg: dict) -> None:
    evento = msg["event"]
    if modulo == "frota":
        if evento == "PosicaoAtualizada":
            print(f"[frota] veiculo {msg['vehicleId']} em ({msg['latitude']}, {msg['longitude']})")
        elif evento == "DispositivoOffline":
            print(f"[frota] sensor do veiculo {msg['vehicleId']} sem sinal ha {msg['segundosSemSinal']}s")
        elif evento == "AlertaTemperatura":
            print(f"[frota] ALERTA {msg['severidade']} na viagem {msg['tripId']}: avisar o motorista")
    elif modulo == "financeiro":
        if evento == "AlertaTemperatura":
            print(f"[financeiro] carga {msg['shipmentId']} em violacao ({msg['tipo']}), aguardando encerramento")
        elif evento == "AlertaTemperaturaEncerrado":
            minutos = msg["duracaoSegundos"] / 60
            print(f"[financeiro] carga {msg['shipmentId']}: {minutos:.1f} min fora da faixa -> calcular ajuste")


def main() -> None:
    modulo = sys.argv[1] if len(sys.argv) > 1 else "frota"
    fila = f"{modulo}.tracking.events"

    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    canal = conn.channel()
    canal.queue_declare(fila, passive=True)  # erro aqui = definicoes do RabbitMQ nao foram carregadas
    canal.basic_qos(prefetch_count=10)

    def callback(ch, method, _props, corpo):
        try:
            msg = json.loads(corpo)
            if msg["eventId"] not in processados:  # idempotencia
                tratar(modulo, msg)
                processados.add(msg["eventId"])
            ch.basic_ack(method.delivery_tag)
        except Exception as erro:
            print(f"[{modulo}] mensagem enviada para a DLQ: {erro}")
            ch.basic_nack(method.delivery_tag, requeue=False)

    canal.basic_consume(fila, callback)
    print(f"Consumindo {fila}. Ctrl+C para sair.")
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        conn.close()


if __name__ == "__main__":
    main()
