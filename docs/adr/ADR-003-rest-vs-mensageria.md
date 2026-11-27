# ADR-003 — REST vs mensageria

**Status:** aceito

**Contexto:** o sensor envia leituras; Fleet, Finance e CRM precisam reagir a elas.

**Problema:** onde usar chamada síncrona e onde usar evento?

**Alternativas:**
1. Tudo REST (o Track chama a API de cada squad).
2. Tudo mensageria (inclusive o sensor publicando direto no RabbitMQ via MQTT).
3. Híbrido: sensor → REST; Track → outros squads por eventos; consultas por REST.

**Decisão:** alternativa 3. Exchange `topic` compartilhado `siglog.events`, routing key `tracking.<Evento>`, envelope JSON versionado.

**Justificativa:** HTTP é o mais simples e confiável no ESP32 e permite autenticar e validar antes de aceitar a leitura. Eventos desacoplam: o Track não sabe quem consome, e cada squad cria a própria fila. Consultas (localização, histórico) são naturalmente síncronas.

**Consequências:** consumidores precisam ser idempotentes (`eventId`); mudanças no payload exigem versionamento (`version`) e o teste de contrato.
