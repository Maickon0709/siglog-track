# ADR-005 — Estratégia de segurança

**Status:** aceito

**Contexto:** o sensor é um microcontrolador com pouca memória; as consultas expõem a localização de cargas.

**Alternativas para o sensor:** sem autenticação; chave por header; mTLS com certificado por dispositivo.

**Decisão:** chave `X-Device-Key` no sensor; **chave `X-API-Key` por squad** para as chamadas entre módulos, com permissão de escrita (`POST /devices`) só para WMS e Fleet; validação de faixa nos dados, container sem root, Trivy e SonarQube no CI. JWT para usuários finais (⏳).

**Justificativa:** a chave cabe no ESP32 e barra envio anônimo; a chave por squad identifica quem chamou (log e métrica) e pode ser revogada de um squad sem afetar os outros, sem exigir um servidor de identidade. mTLS e OAuth2 ficam como evolução.

**Consequências:** a chave precisa ser trocada do valor padrão e rotacionada; sem HTTPS na rede local, ela trafega em texto — aceitável no laboratório, não em produção.
