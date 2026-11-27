# Contrato de Eventos — SIG-Log Track (Squad 03)

Este é o contrato que o Track publica para os outros módulos. Ele é **independente de linguagem**:
qualquer módulo (Python, Java, Node, C#...) consome lendo JSON de uma fila do RabbitMQ, sem importar
código do Track.

Segue a **mesma convenção do WMS** ([Projeto-WMS-](https://github.com/ViniciusNascimento99/Projeto-WMS-)),
para que todos os módulos da plataforma falem igual.

| Arquivo | Conteúdo |
|---|---|
| [`events.schema.json`](events.schema.json) | JSON Schema (draft 2020-12), um bloco por evento |
| [`events.examples.json`](events.examples.json) | Um exemplo válido de cada evento |
| [`../monitoring/rabbitmq/definitions.json`](../monitoring/rabbitmq/definitions.json) | Exchanges, filas, DLQs e bindings |
| [`openapi.yaml`](openapi.yaml) | API REST |

## 1. Convenção de mensageria da plataforma

| Item | Padrão | No Track |
|---|---|---|
| Exchange | um `topic` por módulo produtor: `siglog.<modulo>.events` | `siglog.tracking.events` |
| Routing key | `<modulo>.<evento.em.minusculas.com.pontos>.v<versao>` | `tracking.alerta.temperatura.v1` |
| Fila | uma por consumidor e produtor: `<consumidor>.<produtor>.events` | `financeiro.tracking.events` |
| Fila de erro | `<fila>.dlq`, via exchange `siglog.<produtor>.dlx` | `financeiro.tracking.events.dlq` |
| Tipo de fila | `quorum`, durável | — |
| Mensagem | JSON UTF-8, persistente (`delivery_mode=2`) | — |
| Nomes dos módulos | `wms`, `frota`, `tracking`, `financeiro`, `rh`, `crm` | — |

As filas de quem consome o Track **já são criadas** pelo `definitions.json` do Track:

| Fila | Eventos que recebe |
|---|---|
| `frota.tracking.events` | `PosicaoAtualizada`, `DispositivoOffline`, `AlertaTemperatura` |
| `financeiro.tracking.events` | `AlertaTemperatura`, `AlertaTemperaturaEncerrado` |
| `crm.tracking.events` | `PosicaoAtualizada`, `AlertaTemperatura`, `AlertaTemperaturaEncerrado`, `DispositivoOffline` |

> `TemperaturaAtualizada` (1 mensagem a cada ~10 s por sensor) não vai para nenhuma fila por padrão.
> Quem quiser a série completa consulta `GET /shipments/{id}/history` ou pede um binding novo.

## 2. Formato da mensagem

Campos de controle **na raiz**, seguidos dos dados do evento (sem bloco `data`), como no WMS:

```json
{
  "event": "AlertaTemperatura",
  "version": 1,
  "eventId": "3f2b8c1e-9a4d-4e57-b6a2-1c0d9e8f7a65",
  "timestamp": "2026-11-26T14:00:00Z",
  "correlationId": "EXP-001",
  "source": "tracking",
  "deviceId": "IOT-001",
  "shipmentId": "EXP-001",
  "vehicleId": "VEI-042",
  "tripId": "VIA-2026-0917",
  "...": "campos do evento"
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `event` | string | Nome do evento em PascalCase |
| `version` | int | Versão do formato. Igual ao `v1` da routing key |
| `eventId` | UUID | Único por mensagem. **Use para idempotência** |
| `timestamp` | ISO-8601 UTC, sem frações (`2026-11-26T14:00:00Z`) | Quando aconteceu |
| `correlationId` | string | `shipmentId` da carga |
| `source` | `"tracking"` | Módulo que publicou |
| `deviceId`, `shipmentId` | string | Sempre presentes |
| `vehicleId`, `tripId` | string ou `null` | Vêm da Frota, quando o sensor foi vinculado a uma viagem |

O schema usa `additionalProperties: false`, assim como o do WMS: **qualquer mudança nos campos gera uma
nova versão** (`v2`, com routing key nova), e a `v1` continua sendo publicada até todos migrarem.

## 3. Identificadores compartilhados

| Campo | Dono | Exemplo |
|---|---|---|
| `shipmentId` | WMS (`CargaExpedida`) | `EXP-001` |
| `vehicleId`, `tripId` | Frota | `VEI-042`, `VIA-2026-0917` |
| `deviceId` | Track | `IOT-001` |

## 4. Eventos publicados

Exemplos completos em [`events.examples.json`](events.examples.json).

| Evento | Routing key | Quando | Campos próprios |
|---|---|---|---|
| `TemperaturaAtualizada` | `tracking.temperatura.atualizada.v1` | A cada leitura | `temperatura`, `umidade`, `bateria`, `dentroDaFaixa` |
| `PosicaoAtualizada` | `tracking.posicao.atualizada.v1` | Leitura com GPS | `latitude`, `longitude` |
| `AlertaTemperatura` | `tracking.alerta.temperatura.v1` | 3 leituras seguidas fora da faixa (uma vez por violação) | `alertId`, `tipo`, `valor`, `limiteMin`, `limiteMax`, `tipoCarga`, `severidade`, `inicioViolacao` |
| `AlertaTemperaturaEncerrado` | `tracking.alerta.temperatura.encerrado.v1` | Condição normalizou | `alertId`, `tipo`, `valorExtremo`, `inicioViolacao`, `fimViolacao`, `duracaoSegundos` |
| `DispositivoOffline` | `tracking.dispositivo.offline.v1` | Sem leitura há mais de 60 s | `ultimaLeitura`, `segundosSemSinal` |

- `tipo`: `TEMPERATURA_ALTA` · `TEMPERATURA_BAIXA` · `UMIDADE_ALTA`
- `severidade`: `ALERTA` (até 2 °C / 10 % além do limite) · `CRITICA` (acima disso)
- O **Financeiro** usa `duracaoSegundos` do `AlertaTemperaturaEncerrado` para calcular multa, desconto ou indenização.

## 5. Eventos consumidos

| Fila do Track | Produtor | Routing keys | O que o Track faz |
|---|---|---|---|
| `tracking.wms.events` | WMS | `wms.carga.expedida.v1` | Carga passa a `EM_TRANSITO` (UC09, `GET /shipments/{id}`) |
| | | `wms.mercadoria.recebida.v1`, `wms.produto.armazenado.v1` | Recebidos e ignorados (ack) |

Mensagem que não é JSON ou que quebra o processamento vai para `tracking.wms.events.dlq`.

## 6. Regras para quem consome

1. **Idempotência:** guarde os `eventId` processados; o RabbitMQ pode reentregar.
2. **ack** só depois de gravar no seu banco; **nack sem requeue** para mandar uma mensagem com erro para a DLQ.
3. Campos `null` permitidos: `vehicleId`, `tripId`, `umidade`, `bateria`, `limiteMin`, `limiteMax`.
4. Exemplo pronto: [`scripts/consumidor.py`](../scripts/consumidor.py).

## 7. API REST do Track

Documentação interativa: `http://<host>:8000/docs`. Rotas com 🔑 exigem `X-API-Key` (seção 8).

| Método | Rota | Quem usa |
|---|---|---|
| `POST` | `/devices` 🔑 | WMS, Frota: vincula sensor ↔ carga ↔ veículo ↔ viagem |
| `GET` | `/devices/{deviceId}` 🔑 | Todos |
| `POST` | `/sensor-readings` | O sensor ESP32 (`X-Device-Key`) |
| `GET` | `/shipments/{shipmentId}` 🔑 | Todos: status da carga (UC09) |
| `GET` | `/shipments/{shipmentId}/location` 🔑 | CRM, Frota |
| `GET` | `/shipments/{shipmentId}/history` 🔑 | CRM, Financeiro |
| `GET` | `/alerts?shipmentId=` 🔑 | CRM, Financeiro |

## 8. Chaves de API entre squads

Toda chamada REST de outro squad para o Track precisa do header **`X-API-Key`** com a chave **do squad que
está chamando**. O Squad 03 gera uma chave para cada squad e entrega por canal privado (nunca no Git nem no
grupo da turma).

```bash
curl -H "X-API-Key: <chave-do-seu-squad>" http://<host-do-track>:8000/shipments/EXP-001/location
```

| Squad | Pode consultar (`GET`) | Pode vincular sensor (`POST /devices`) |
|---|---|---|
| 01 — WMS | ✅ | ✅ |
| 02 — Fleet | ✅ | ✅ |
| 04 — Finance | ✅ | ❌ (403) |
| 05 — People | ✅ | ❌ (403) |
| 06 — CRM | ✅ | ❌ (403) |

| Resposta | Significado |
|---|---|
| `401` | Chave ausente ou inválida |
| `403` | Chave válida, mas o squad não tem permissão para a operação |

- `/health` e `/metrics` são públicos; `/sensor-readings` usa a chave do sensor (`X-Device-Key`), não a de squad.
- No ambiente local (`docker compose`) as chaves de desenvolvimento são `dev-wms`, `dev-fleet`, `dev-finance`,
  `dev-people` e `dev-crm`. Em produção elas vêm da variável `SQUAD_API_KEYS` (secret).

### Chamadas no sentido contrário
Quando o Track precisar chamar a API de outro squad, usa a chave que **aquele squad** entregar ao Track,
guardada como secret (ex.: `FLEET_API_KEY`). Cada squad é dono das chaves da própria API.

> ⚠️ **Em aberto:** o WMS autentica com **JWT** (`Authorization: Bearer`, segredo `JWT_SECRET`
> compartilhado). A turma precisa escolher um padrão único; o Track pode aceitar os dois.

### RabbitMQ
A chave de API vale para o REST. Para a mensageria, o ideal é cada squad ter **seu próprio usuário no RabbitMQ**,
com permissão só nas filas dele (`frota.*`, `financeiro.*`...). Isso precisa ser combinado entre
todos os squads, junto com quem hospeda o broker compartilhado.
