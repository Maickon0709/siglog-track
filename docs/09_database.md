# 09 — Banco de Dados

## Estado atual
`src/infrastructure/repositorio.py` guarda tudo **em memória** (perde ao reiniciar). Serve para desenvolvimento e testes.

## Alvo: MongoDB (Database-per-Service)
O kit indica MongoDB para telemetria: alto volume e formato semiestruturado (ver [ADR-002](adr/ADR-002-banco-de-dados.md)).

| Coleção | Documento | Índices |
|---|---|---|
| `dispositivos` | `{_id: deviceId, shipmentId, vehicleId, tripId, tipoCarga, faixa{...}, estado{...}}` | `shipmentId` |
| `leituras` | `{deviceId, shipmentId, timestamp, temperatura, umidade, bateria, localizacao: GeoJSON Point}` | `{shipmentId, timestamp}`, `2dsphere` em `localizacao`, TTL opcional |
| `alertas` | `{alertId, shipmentId, tipo, valor, severidade, inicio, fim, duracaoSegundos, status}` | `{shipmentId, status}` |

Sugestão: `leituras` como **time-series collection** (MongoDB 5+), com `timeField: timestamp` e `metaField: deviceId`.

✏️ Tarefa: criar `RepositorioMongo` com os mesmos métodos de `RepositorioEmMemoria` e adicionar o serviço `mongodb` no compose.
