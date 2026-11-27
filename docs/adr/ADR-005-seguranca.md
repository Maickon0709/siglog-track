# ADR-005 — Estratégia de segurança

**Status:** aceito

**Contexto:** o sensor é um microcontrolador com pouca memória; as consultas expõem a localização de cargas.

**Alternativas para o sensor:** sem autenticação; chave por header; mTLS com certificado por dispositivo.

**Decisão:** chave `X-Device-Key` no sensor (comparação em tempo constante), validação de faixa nos dados, container sem root, Trivy e SonarQube no CI. JWT para usuários e squads (⏳).

**Justificativa:** a chave cabe no ESP32 e barra envio anônimo; mTLS fica como evolução.

**Consequências:** a chave precisa ser trocada do valor padrão e rotacionada; sem HTTPS na rede local, ela trafega em texto — aceitável no laboratório, não em produção.
