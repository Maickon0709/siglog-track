# 02 — Requisitos

## Casos de uso
| Código | Caso de uso | Status |
|---|---|---|
| UC01 | Registrar dispositivo | ✅ `POST /devices` |
| UC02 | Receber posição | ✅ `POST /sensor-readings` (lat/long) |
| UC03 | Receber temperatura | ✅ `POST /sensor-readings` |
| UC04 | Receber umidade | ✅ `POST /sensor-readings` |
| UC05 | Consultar localização | ✅ `GET /shipments/{id}/location` |
| UC06 | Consultar histórico | ✅ `GET /shipments/{id}/history` |
| UC07 | Detectar condição crítica | ✅ regra de faixa + 3 leituras seguidas |
| UC08 | Gerar alerta | ✅ `AlertaTemperatura` / `GET /alerts` |
| UC09 | Atualizar status da carga | ⏳ pendente |

## Requisitos funcionais
| Código | Descrição |
|---|---|
| RF01 | Cadastrar um sensor e vinculá-lo a carga, veículo e viagem |
| RF02 | Receber leituras de temperatura, umidade, bateria e posição |
| RF03 | Aplicar a faixa de temperatura e umidade conforme o tipo de carga |
| RF04 | Gerar alerta após N leituras seguidas fora da faixa (padrão 3) |
| RF05 | Encerrar o alerta quando a condição normalizar, informando a duração |
| RF06 | Detectar dispositivo sem comunicação (padrão 60 s) |
| RF07 | Detectar carga fora da rota (⏳ depende da rota do Fleet) |
| RF08 | Publicar eventos no RabbitMQ para os outros squads |
| RF09 | Consultar localização atual, histórico e alertas |

## Requisitos não funcionais
| Código | Descrição |
|---|---|
| RNF01 | Aceitar 100 req/s com p95 < 200 ms (cenário normal) |
| RNF02 | Leituras não podem ser perdidas se o RabbitMQ cair (ficam no histórico, a falha é medida) |
| RNF03 | Só sensores com `X-Device-Key` válida enviam leituras |
| RNF04 | Logs estruturados JSON, métricas Prometheus e traces |
| RNF05 | Sobe com um único `docker compose up` |
| RNF06 | Contrato de eventos versionado e validado por teste |
