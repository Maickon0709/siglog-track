# Contrato de Eventos — SIG-Log Track (Squad 03)

Este é o contrato que o Track publica para os outros squads. Ele é **independente
de linguagem**: qualquer squad (Python, Java, Node, C#...) consome lendo JSON de
uma fila do RabbitMQ. Nenhum squad precisa importar código do Track.

Schema formal: [`evento.schema.json`](evento.schema.json) (JSON Schema draft 2020-12).

## 1. Onde os eventos são publicados

| Item | Valor |
|---|---|
| Broker | RabbitMQ (AMQP 0-9-1, porta 5672) |
| Exchange | `siglog.events` |
| Tipo do exchange | `topic`, durável |
| Routing key | `tracking.<NomeDoEvento>` (ex.: `tracking.AlertaTemperatura`) |
| Content-Type | `application/json`, UTF-8 |
| Entrega | mensagens persistentes (`delivery_mode=2`) |

Cada squad cria **a própria fila** e faz o bind só no que interessa:

| Squad | Fila sugerida | Binding keys |
|---|---|---|
| 02 — Fleet | `fleet.tracking` | `tracking.PosicaoAtualizada`, `tracking.DispositivoOffline`, `tracking.AlertaTemperatura` |
| 04 — Finance | `finance.tracking` | `tracking.AlertaTemperatura`, `tracking.AlertaTemperaturaEncerrado` |
| 06 — CRM | `crm.tracking` | `tracking.#` |

> O exchange `siglog.events` é compartilhado pela plataforma. Os outros squads
> publicam nele com o prefixo deles (`fleet.*`, `finance.*`, `wms.*`...).

## 2. Envelope (igual para todos os eventos)

```json
{
  "event": "AlertaTemperatura",
  "eventId": "7c1e0f7e-3c1b-4a43-9a51-0c5b0d4c2a11",
  "version": 1,
  "source": "siglog-track",
  "timestamp": "2026-11-26T14:00:00Z",
  "correlationId": "EXP-001",
  "data": { }
}
```

| Campo | Tipo | Descrição |
|---|---|---|
| `event` | string | Nome do evento (igual ao final da routing key). |
| `eventId` | UUID | Único por mensagem. **Use para idempotência** (ignore IDs repetidos). |
| `version` | int | Versão do formato de `data`. Mudança incompatível → nova versão. |
| `source` | string | Sempre `siglog-track`. |
| `timestamp` | ISO-8601 UTC | Quando o evento aconteceu. |
| `correlationId` | string \| null | `shipmentId` da carga; usado para tracing entre squads. |
| `data` | objeto | Conteúdo específico do evento (abaixo). |

## 3. Identificadores compartilhados

Os IDs abaixo **não são criados pelo Track**: vêm dos outros squads e são
associados ao sensor no `POST /devices`.

| Campo | Dono | Exemplo |
|---|---|---|
| `shipmentId` | Squad 01 (WMS, evento `CargaExpedida`) | `EXP-001` |
| `vehicleId` | Squad 02 (Fleet) | `VEI-042` |
| `tripId` | Squad 02 (Fleet) | `VIA-2026-0917` |
| `deviceId` | Squad 03 (Track) | `IOT-001` |

## 4. Eventos

### TemperaturaAtualizada
Uma leitura válida do sensor. Volume alto (1 a cada ~10 s por sensor).
```json
"data": {
  "deviceId": "IOT-001", "shipmentId": "EXP-001",
  "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
  "temperatura": 5.2, "umidade": 61.0, "bateria": 88,
  "dentroDaFaixa": true
}
```

### PosicaoAtualizada
Publicado quando a leitura traz latitude/longitude.
```json
"data": {
  "deviceId": "IOT-001", "shipmentId": "EXP-001",
  "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
  "latitude": -23.5505, "longitude": -46.6333
}
```

### AlertaTemperatura
Temperatura ou umidade fora da faixa por **N leituras seguidas** (padrão 3).
Publicado **uma vez** por violação, não a cada leitura.
```json
"data": {
  "alertId": "ALT-3f9a2c", "deviceId": "IOT-001", "shipmentId": "EXP-001",
  "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
  "tipo": "TEMPERATURA_ALTA",
  "valor": 9.4, "limiteMin": 2.0, "limiteMax": 8.0,
  "tipoCarga": "VACINA",
  "severidade": "CRITICA",
  "inicioViolacao": "2026-11-26T13:59:30Z"
}
```
`tipo`: `TEMPERATURA_ALTA` | `TEMPERATURA_BAIXA` | `UMIDADE_ALTA`
`severidade`: `ALERTA` (até 2 °C / 10 % além do limite) | `CRITICA` (acima disso)

### AlertaTemperaturaEncerrado
A condição voltou ao normal. Traz a **duração**, que o Finance usa para calcular
multa/desconto/indenização.
```json
"data": {
  "alertId": "ALT-3f9a2c", "deviceId": "IOT-001", "shipmentId": "EXP-001",
  "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
  "tipo": "TEMPERATURA_ALTA",
  "valorExtremo": 11.8,
  "inicioViolacao": "2026-11-26T13:59:30Z",
  "fimViolacao": "2026-11-26T14:21:10Z",
  "duracaoSegundos": 1300
}
```

### DispositivoOffline
O sensor ficou sem enviar leituras por mais de `OFFLINE_SEGUNDOS` (padrão 60).
```json
"data": {
  "deviceId": "IOT-001", "shipmentId": "EXP-001",
  "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
  "ultimaLeitura": "2026-11-26T14:00:00Z", "segundosSemSinal": 75
}
```

## 5. Regras para quem consome

1. **Idempotência:** guarde os `eventId` processados; o RabbitMQ pode reentregar.
2. **Ignore campos desconhecidos:** o Track pode adicionar campos novos em `data`
   sem mudar `version`. Remover ou renomear campo sempre muda `version`.
3. **Campos opcionais** (`vehicleId`, `tripId`, `umidade`, `bateria`) podem vir `null`.
4. **ack manual:** só dê `ack` depois de gravar no seu banco.

## 6. API REST do Track usada pelos outros squads

Documentação interativa (OpenAPI gerado automaticamente): `http://<host>:8000/docs`

| Método | Rota | Quem usa |
|---|---|---|
| `POST` | `/devices` | Fleet/Track: vincula sensor ↔ carga ↔ veículo ↔ viagem |
| `GET` | `/devices/{deviceId}` | Todos |
| `POST` | `/sensor-readings` | O próprio sensor ESP32 |
| `GET` | `/shipments/{shipmentId}/location` | CRM, Fleet |
| `GET` | `/shipments/{shipmentId}/history` | CRM, Finance |
| `GET` | `/alerts?shipmentId=` | CRM, Finance |

## 7. Chaves de API entre squads

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

### RabbitMQ
A chave de API vale para o REST. Para a mensageria, o ideal é cada squad ter **seu próprio usuário no RabbitMQ**,
com permissão só nas filas com o prefixo dele (`fleet.*`, `finance.*`...). Isso precisa ser combinado entre
todos os squads, junto com quem hospeda o broker compartilhado.
