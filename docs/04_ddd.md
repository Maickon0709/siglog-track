# 04 — Domain-Driven Design

## Linguagem ubíqua
| Termo | Significado |
|---|---|
| Dispositivo (DispositivoIoT) | Sensor físico (ESP32 + DHT22) identificado por `deviceId` |
| Leitura (LeituraSensor) | Uma medição: temperatura, umidade, bateria, posição e horário |
| Faixa | Limites aceitáveis de temperatura e umidade para um tipo de carga |
| Violação | Sequência de leituras fora da faixa |
| Alerta | Violação confirmada (N leituras seguidas) |
| Offline | Dispositivo sem enviar leituras além do limite |

## Agregado principal: `Dispositivo`
Guarda o vínculo (carga, veículo, viagem), a faixa e o estado das violações. Toda regra passa por ele
(`src/domain/monitoramento.py`), garantindo as invariantes:
- um alerta por tipo de violação ativo de cada vez;
- alerta só após N leituras seguidas;
- `DispositivoOffline` emitido uma única vez até o sensor voltar.

## Entidades e objetos de valor
| Kit | Implementação |
|---|---|
| DispositivoIoT | `Dispositivo` (agregado) |
| LeituraSensor | `Leitura` (objeto de valor imutável) |
| Alerta | `Violacao` + registro em `/alerts` |
| Localizacao | campos `latitude`/`longitude` da leitura |
| HistoricoTracking | histórico por `shipmentId` no repositório |
| Carga, Rota | referências externas (`shipmentId` do WMS, `tripId` do Fleet) |
| EventoTelemetria | eventos de domínio publicados (ver 08) |

## Comandos → Eventos (Event Storming)
| Ator | Comando | Agregado | Evento |
|---|---|---|---|
| Fleet / operador | RegistrarDispositivo | Dispositivo | DispositivoRegistrado (log) |
| Sensor | EnviarLeitura | Dispositivo | TemperaturaAtualizada, PosicaoAtualizada |
| Regra (política) | — | Dispositivo | AlertaTemperatura |
| Regra (política) | — | Dispositivo | AlertaTemperaturaEncerrado |
| Relógio (monitor) | VerificarOffline | Dispositivo | DispositivoOffline |
| WMS | (externo) | — | CargaExpedida → vincula sensor (⏳) |
