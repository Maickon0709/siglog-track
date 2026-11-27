# 11 — Segurança

| Pergunta do kit | Resposta |
|---|---|
| Quais dados são sensíveis? | Localização de cargas e veículos (risco de roubo), dados de clientes ligados ao `shipmentId` |
| Quem pode acessar? | Sensor: só envia leituras. Squads e operadores: consultas. Só o Fleet/operador vincula sensores |
| Como autenticar? | Sensor: header `X-Device-Key` (✅, comparação em tempo constante). Usuários e squads: JWT/OAuth2 (⏳) |
| Como autorizar? | Escopos por cliente: `telemetry:write`, `tracking:read`, `devices:admin` (⏳) |
| Como proteger as APIs? | Validação de entrada (Pydantic, ✅), HTTPS no gateway (⏳), rate limit (⏳), usuário sem root no container (✅) |

## Pipeline DevSecOps
- **Trivy:** dependências, segredos e Dockerfile (`fs`) + imagem final (`image`) no CI.
- **SonarQube/SonarCloud:** roda quando o secret `SONAR_TOKEN` está configurado.

## Pontos de atenção
- `DEVICE_API_KEY` padrão é só para desenvolvimento: troquem via variável de ambiente/secret.
- `config.h` do firmware (senha do Wi-Fi) está no `.gitignore`: **nunca** commitem.
- RabbitMQ com `guest/guest` só vale localmente.
