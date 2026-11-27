# 08 — Catálogo de Eventos

O contrato completo, com exemplos de cada payload, está em [`contracts/CONTRATO_EVENTOS.md`](../contracts/CONTRATO_EVENTOS.md),
e o schema formal em [`contracts/evento.schema.json`](../contracts/evento.schema.json).

| Evento | Routing key | Quando | Consumidores |
|---|---|---|---|
| TemperaturaAtualizada | `tracking.TemperaturaAtualizada` | A cada leitura | CRM |
| PosicaoAtualizada | `tracking.PosicaoAtualizada` | Leitura com lat/long | Fleet, CRM |
| AlertaTemperatura | `tracking.AlertaTemperatura` | N leituras seguidas fora da faixa | Fleet, Finance, CRM |
| AlertaTemperaturaEncerrado | `tracking.AlertaTemperaturaEncerrado` | Condição normalizou (traz a duração) | Finance, CRM |
| DispositivoOffline | `tracking.DispositivoOffline` | Sem leitura há mais de 60 s | Fleet, CRM |
| CargaForaDaRota | `tracking.CargaForaDaRota` | ⏳ pendente | Fleet, CRM |

## Eventos consumidos (⏳)
| Evento | Produtor | Uso no Track |
|---|---|---|
| CargaExpedida | WMS | Vincular o sensor à carga automaticamente |
| ✏️ rota/viagem | Fleet | Detectar `CargaForaDaRota` |

## Filas RabbitMQ
Exchange `siglog.events` (topic, durável). Cada consumidor cria a própria fila:
`fleet.tracking`, `finance.tracking`, `crm.tracking`. Exemplo de consumidor em [`scripts/consumidor.py`](../scripts/consumidor.py).
