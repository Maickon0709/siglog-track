# ADR-002 — Banco de dados

**Status:** aceito (implementação ⏳)

**Contexto:** telemetria gera muitas escritas pequenas (1 leitura a cada 10 s por sensor), com campos opcionais (umidade, GPS, bateria).

**Problema:** qual banco usar, respeitando o padrão Database-per-Service?

**Alternativas:** PostgreSQL (com TimescaleDB), MongoDB, InfluxDB.

**Decisão:** MongoDB, com `leituras` como time-series collection e índice geoespacial.

**Justificativa:** é o exemplo indicado pelo kit para IoT; aceita documento semiestruturado sem migração; time-series e `2dsphere` atendem histórico e localização.

**Consequências:** o squad mantém um banco diferente dos outros (que usam PostgreSQL); consultas relacionais entre squads são impossíveis, e tudo passa por API ou eventos (é o objetivo do Database-per-Service).
