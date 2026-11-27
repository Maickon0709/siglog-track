# 08 — Catálogo de Eventos

O Track segue a **convenção de mensageria do WMS**: um exchange `topic` por módulo, routing key
`<modulo>.<evento.em.pontos>.v1`, uma fila por consumidor com DLQ e campos na raiz da mensagem.

Contrato completo: [`contracts/CONTRATO_EVENTOS.md`](../contracts/CONTRATO_EVENTOS.md) ·
schema: [`events.schema.json`](../contracts/events.schema.json) ·
exemplos: [`events.examples.json`](../contracts/events.examples.json) ·
filas: [`definitions.json`](../monitoring/rabbitmq/definitions.json).

## Publicados (exchange `siglog.tracking.events`)
| Evento | Routing key | Filas |
|---|---|---|
| TemperaturaAtualizada | `tracking.temperatura.atualizada.v1` | — (alto volume; consultar via REST) |
| PosicaoAtualizada | `tracking.posicao.atualizada.v1` | frota, crm |
| AlertaTemperatura | `tracking.alerta.temperatura.v1` | frota, financeiro, crm |
| AlertaTemperaturaEncerrado | `tracking.alerta.temperatura.encerrado.v1` | financeiro, crm |
| DispositivoOffline | `tracking.dispositivo.offline.v1` | frota, crm |
| CargaForaDaRota | `tracking.carga.fora.da.rota.v1` | ⏳ pendente |

As filas são `<consumidor>.tracking.events`, cada uma com `<fila>.dlq` via `siglog.tracking.dlx`.

## Consumidos (fila `tracking.wms.events`)
| Evento | Routing key | Uso no Track |
|---|---|---|
| CargaExpedida | `wms.carga.expedida.v1` | ✅ carga passa a `EM_TRANSITO` (UC09) |
| MercadoriaRecebida, ProdutoArmazenado | `wms.mercadoria.recebida.v1`, `wms.produto.armazenado.v1` | Ignorados (ack) |
| ✏️ rota/viagem | Frota | ⏳ necessário para `CargaForaDaRota` |
