# 10 — Observabilidade

O kit diz que o Track é **o squad que mais precisa demonstrar observabilidade**: logs, métricas e traces.

## Logs (✅)
JSON no formato do kit, um por linha:
```json
{"timestamp": "2026-11-26T14:00:00Z", "service": "siglog-track", "event": "AlertaTemperatura", "level": "INFO", "eventId": "…", "shipmentId": "EXP-001"}
```

## Métricas (✅) — `GET /metrics`
| Métrica | Tipo | Uso no Grafana |
|---|---|---|
| `track_leituras_total{device_id}` | counter | Leituras/min (= requests/min) |
| `track_eventos_publicados_total{evento}` | counter | Mensagens publicadas |
| `track_eventos_consumidos_total{source,evento}` | counter | Mensagens consumidas de outros módulos |
| `track_erros_publicacao_total` | counter | Taxa de erros com o RabbitMQ |
| `track_alertas_ativos` | gauge | Alertas |
| `track_temperatura_celsius{device_id,shipment_id}` | gauge | Temperatura ao vivo |
| `track_umidade_percent{…}` | gauge | Umidade |
| `track_dispositivos_online` | gauge | Dispositivos online |

⏳ Falta para o dashboard comum: latência e taxa de erros HTTP (`request_duration`, `errors_total`, `active_requests`).
Sugestão: `prometheus-fastapi-instrumentator` ou a instrumentação do OpenTelemetry.

## Dashboard (✅)
`monitoring/grafana/dashboards/siglog-track.json` é carregado automaticamente: http://localhost:3000.

## Traces (⏳)
Plano: OpenTelemetry (`opentelemetry-instrumentation-fastapi` + `-pika`), exportando para Jaeger, e propagar o
`traceparent` nos headers da mensagem do RabbitMQ para o trace continuar no Fleet e no Finance.
