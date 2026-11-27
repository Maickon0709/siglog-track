# 07 — Contrato de API

O contrato oficial é o [`contracts/openapi.yaml`](../contracts/openapi.yaml), gerado a partir do código:
```bash
python -m scripts.exportar_openapi
```
O teste `tests/contract/test_contrato_eventos.py::test_openapi_publicado_esta_atualizado` falha se alguém mudar uma rota
e esquecer de regerar o arquivo.

Com o serviço no ar, a documentação interativa fica em `http://localhost:8000/docs`.

Rotas marcadas com 🔑 exigem o header `X-API-Key` do squad (401 sem chave, 403 sem permissão).

| Método | Rota | Sucesso | Erros | Quem usa |
|---|---|---|---|---|
| POST | `/devices` 🔑 | 201 | 401, 403, 422 | WMS, Fleet |
| GET | `/devices/{deviceId}` 🔑 | 200 | 401, 404 | Todos |
| POST | `/sensor-readings` | 202 | 401 chave inválida, 404 sensor não vinculado, 422 dados inválidos | ESP32 |
| GET | `/shipments/{shipmentId}/location` 🔑 | 200 | 401, 404 | CRM, Fleet |
| GET | `/shipments/{shipmentId}/history?limit=` 🔑 | 200 | 401, 422 | CRM, Finance |
| GET | `/alerts?shipmentId=` 🔑 | 200 | 401 | CRM, Finance |
| GET | `/health` | 200 | — | Docker / monitoramento |
| GET | `/metrics` | 200 | — | Prometheus |

> ⏳ O kit também cita `POST /telemetry` e `POST /locations`. Decisão do squad: ✏️ implementar como aliases de
> `/sensor-readings` ou registrar em ADR por que foram unificados.
