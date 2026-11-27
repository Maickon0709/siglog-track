# ADR-001 — Arquitetura do serviço

**Status:** aceito

**Contexto:** o Track recebe dados de sensores físicos e precisa publicar eventos para três squads, com regras de domínio claras e testáveis.

**Problema:** como organizar o serviço sem cair num monólito acoplado nem numa arquitetura complexa demais para o semestre?

**Alternativas:**
1. Script único que recebe e publica.
2. Microsserviço em camadas (API, Application, Domain, Infrastructure) — padrão do kit.
3. Arquitetura hexagonal completa com portas e adaptadores para tudo.

**Decisão:** alternativa 2, em Python com FastAPI. O ESP32 fala só HTTP com o serviço e nunca acessa o RabbitMQ direto.

**Justificativa:** o domínio fica puro e testável (`src/domain` sem dependências); o FastAPI gera o OpenAPI automaticamente; o sensor fica simples e não precisa de biblioteca AMQP.

**Consequências:** o serviço vira o ponto único de entrada da telemetria, então precisa escalar (ver ATAM, cenário 4). Trocar o repositório ou o broker afeta só a infraestrutura.
