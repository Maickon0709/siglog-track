# ADR-003 — REST vs mensageria

**Status:** aceito

**Contexto:** o sensor envia leituras; Fleet, Finance e CRM precisam reagir a elas.

**Problema:** onde usar chamada síncrona e onde usar evento?

**Alternativas:**
1. Tudo REST (o Track chama a API de cada squad).
2. Tudo mensageria (inclusive o sensor publicando direto no RabbitMQ via MQTT).
3. Híbrido: sensor → REST; Track → outros squads por eventos; consultas por REST.

**Decisão:** alternativa 3, seguindo a convenção já adotada pelo WMS: exchange `topic` por módulo (`siglog.tracking.events`), routing key `tracking.<evento.em.pontos>.v1`, fila `<consumidor>.tracking.events` do tipo quorum com DLQ, e mensagem com os campos na raiz.

**Justificativa:** HTTP é o mais simples e confiável no ESP32 e permite autenticar e validar antes de aceitar a leitura. Eventos desacoplam: o Track não sabe quem consome, e cada squad cria a própria fila. Consultas (localização, histórico) são naturalmente síncronas.

**Consequências:** consumidores precisam ser idempotentes (`eventId`); qualquer mudança no payload gera uma nova versão (`v2`) com routing key própria; mensagens com erro vão para a DLQ em vez de travar a fila. Uma primeira versão usava um exchange único `siglog.events`; foi trocada para ficar igual ao WMS.
