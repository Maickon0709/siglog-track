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
