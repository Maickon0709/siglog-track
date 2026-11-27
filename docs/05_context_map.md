# 05 — Context Map

```
        ┌──────────┐  CargaExpedida (⏳)   ┌──────────────┐
        │   WMS    │──────────────────────►│              │
        │ Squad 01 │                       │              │  PosicaoAtualizada
        └──────────┘                       │              │  DispositivoOffline
        ┌──────────┐  rota/viagem (⏳)     │  SIG-Log     │  AlertaTemperatura   ┌──────────┐
        │  Fleet   │──────────────────────►│  TRACK       │─────────────────────►│  Fleet   │
        │ Squad 02 │                       │  Squad 03    │                      └──────────┘
        └──────────┘                       │              │  AlertaTemperatura   ┌──────────┐
   ┌──────────────┐  POST /sensor-readings │              │  ...Encerrado        │ Finance  │
   │ ESP32+DHT22  │───────────────────────►│              │─────────────────────►│ Squad 04 │
   └──────────────┘                        │              │                      └──────────┘
                                           │              │  tracking.#          ┌──────────┐
                                           │              │─────────────────────►│   CRM    │
                                           └──────────────┘  GET /location       │ Squad 06 │
                                                                                 └──────────┘
```

| Relação | Padrão DDD | Observação |
|---|---|---|
| Track → Fleet, Finance, CRM | **Published Language** + Open Host Service | Contrato em `contracts/` (JSON Schema + OpenAPI) |
| WMS → Track | Customer/Supplier | Track consome `CargaExpedida` |
| Fleet → Track | Customer/Supplier | Track precisa da rota para `CargaForaDaRota` |
| Sensor → Track | Conformist | O firmware segue o formato definido pelo Track |
