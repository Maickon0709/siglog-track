# ADR-004 — Estratégia de observabilidade

**Status:** aceito (traces ⏳)

**Contexto:** o kit exige do Track os três pilares (logs, métricas, traces) e um dashboard Grafana.

**Alternativas:** só logs; stack ELK; Prometheus + Grafana + OpenTelemetry/Jaeger.

**Decisão:** logs JSON no stdout, métricas Prometheus em `/metrics`, dashboard Grafana provisionado e OpenTelemetry com Jaeger para traces.

**Justificativa:** é a stack pedida pelo kit, roda no docker compose e o dashboard sobe sem configuração manual.

**Consequências:** métricas por `device_id` têm cardinalidade proporcional ao número de sensores; com milhares de sensores será preciso agregar.
