"""Exemplo de consumidor dos eventos do Track, para os Squads 02 (Fleet) e 04 (Finance).

Copie para o projeto de voces e troque o corpo de `tratar()` pela logica do squad.
Em outra linguagem, a ideia e a mesma: declarar o exchange, criar a fila,
fazer o bind nas routing keys e dar ack depois de processar.

Uso:
    pip install pika
    python scripts/consumidor.py fleet     # fila fleet.tracking
    python scripts/consumidor.py finance   # fila finance.tracking
"""
import json
import os
import sys

import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
EXCHANGE = "siglog.events"

SQUADS = {
    "fleet": ("fleet.tracking", [
        "tracking.PosicaoAtualizada", "tracking.DispositivoOffline", "tracking.AlertaTemperatura",
    ]),
    "finance": ("finance.tracking", [
        "tracking.AlertaTemperatura", "tracking.AlertaTemperaturaEncerrado",
    ]),
}

processados: set[str] = set()  # no projeto real: tabela no banco do squad


def tratar(squad: str, msg: dict) -> None:
    d = msg["data"]
    if squad == "fleet":
        if msg["event"] == "PosicaoAtualizada":
            print(f"[fleet] veiculo {d['vehicleId']} em ({d['latitude']}, {d['longitude']})")
        elif msg["event"] == "DispositivoOffline":
            print(f"[fleet] sensor do veiculo {d['vehicleId']} sem sinal ha {d['segundosSemSinal']}s")
        elif msg["event"] == "AlertaTemperatura":
            print(f"[fleet] ALERTA {d['severidade']} na viagem {d['tripId']}: avisar o motorista")
    elif squad == "finance":
        if msg["event"] == "AlertaTemperatura":
            print(f"[finance] carga {d['shipmentId']} em violacao ({d['tipo']}), aguardando encerramento")
        elif msg["event"] == "AlertaTemperaturaEncerrado":
            minutos = d["duracaoSegundos"] / 60
            print(f"[finance] carga {d['shipmentId']}: {minutos:.1f} min fora da faixa -> calcular ajuste")


def main() -> None:
    squad = sys.argv[1] if len(sys.argv) > 1 else "fleet"
    fila, chaves = SQUADS[squad]

    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    canal = conn.channel()
    canal.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
    canal.queue_declare(fila, durable=True)
    for chave in chaves:
        canal.queue_bind(fila, EXCHANGE, routing_key=chave)
    canal.basic_qos(prefetch_count=10)

    def callback(ch, method, _props, corpo):
        msg = json.loads(corpo)
        if msg["eventId"] not in processados:  # idempotencia
            tratar(squad, msg)
            processados.add(msg["eventId"])
        ch.basic_ack(method.delivery_tag)

    canal.basic_consume(fila, callback)
    print(f"Consumindo {chaves} na fila {fila}. Ctrl+C para sair.")
    try:
        canal.start_consuming()
    except KeyboardInterrupt:
        conn.close()


if __name__ == "__main__":
    main()
