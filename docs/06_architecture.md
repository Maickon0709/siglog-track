# 06 — Arquitetura

## Visão de implantação
```
ESP32 ─HTTP─► track (FastAPI) ─AMQP─► RabbitMQ (exchange siglog.events) ─► Fleet / Finance / CRM
                  │  └─/metrics─► Prometheus ─► Grafana
                  └─ repositório (memória → MongoDB)
```

## Camadas (seção 4 do kit)
| Camada | Pasta | Responsabilidade |
|---|---|---|
| API | `src/api/` | Rotas REST, validação (Pydantic), OpenAPI, autenticação do sensor |
| Application | `src/application/` | Casos de uso (`ServicoTelemetria`), orquestra domínio + infraestrutura |
| Domain | `src/domain/` | Regras puras: faixas, violação, alerta, offline. Sem dependências externas |
| Infrastructure | `src/infrastructure/` | RabbitMQ (`publicador.py`), repositório, métricas |
| Config | `src/config/` | Variáveis de ambiente |
| Observability | `metricas.py` + logs JSON em `api/main.py` | Prometheus e logs (traces ⏳) |

## Decisões principais
Veja os ADRs em [`adr/`](adr/).

## Variáveis de ambiente
| Variável | Padrão | Uso |
|---|---|---|
| `RABBITMQ_URL` | `amqp://guest:guest@localhost:5672/%2F` | Broker |
| `EXCHANGE` | `siglog.events` | Exchange compartilhado da plataforma |
| `DEVICE_API_KEY` | `troque-esta-chave` | Chave do sensor (**trocar em produção**) |
| `OFFLINE_SEGUNDOS` | `60` | Limite para `DispositivoOffline` |
