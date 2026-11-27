# 12 — ATAM

| # | Cenário | Decisão | Benefício | Custo | Trade-off |
|---|---|---|---|---|---|
| 1 | **Performance**: pico de leituras (ex.: frota inteira liga ao mesmo tempo) | Endpoint leve que só valida, aplica a regra em memória e publica; consumidores processam de forma assíncrona | Resposta rápida (202) ao sensor | Lock global no repositório limita o paralelismo | Simplicidade agora vs. particionar por `deviceId` depois |
| 2 | **Disponibilidade**: RabbitMQ fora do ar | A leitura é salva no histórico mesmo se a publicação falhar; reconexão automática; métrica de falhas | Sensor nunca perde a leitura | Eventos daquele período não chegam ao Fleet/Finance | ⏳ Outbox pattern para reenviar depois |
| 3 | **Segurança**: alguém tenta enviar leituras falsas ou ler a localização | `X-Device-Key` no sensor; validação de faixa dos valores; ⏳ JWT nas consultas | Barra envio anônimo | Chave compartilhada por sensor precisa ser rotacionada | Chave simples (cabe no ESP32) vs. mTLS (mais seguro, mais pesado) |
| 4 | **Escalabilidade**: de 10 para 10.000 sensores | Serviço stateless na API + estado no MongoDB; exchange topic deixa cada squad escalar o próprio consumidor | Escala horizontal | Estado de violação precisa sair da memória | ⏳ Mover o estado para o banco ou Redis |
