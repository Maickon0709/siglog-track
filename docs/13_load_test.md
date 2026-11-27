# 13 — Teste de Carga

Script: [`scripts/load/k6_sensor.js`](../scripts/load/k6_sensor.js), que simula vários sensores enviando leituras.

| Cenário | Taxa | Duração | Meta |
|---|---|---|---|
| Normal | 100 req/s | 2 min | p95 < 200 ms, erros < 1 % |
| Pico | 500 req/s | 2 min | p95 < 500 ms, erros < 1 % |
| Extremo | 1000 req/s | 1 min | Descobrir o ponto de quebra |

```bash
docker compose up -d
k6 run -e CENARIO=normal scripts/load/k6_sensor.js
k6 run -e CENARIO=pico scripts/load/k6_sensor.js
k6 run -e CENARIO=extremo scripts/load/k6_sensor.js
```

## Resultados
| Cenário | Média | p95 | p99 | Throughput | Erros |
|---|---|---|---|---|---|
| Normal | ✏️ | ✏️ | ✏️ | ✏️ | ✏️ |
| Pico | ✏️ | ✏️ | ✏️ | ✏️ | ✏️ |
| Extremo | ✏️ | ✏️ | ✏️ | ✏️ | ✏️ |

Anexem prints do Grafana durante cada execução.
