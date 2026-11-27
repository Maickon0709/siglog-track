# 11 — Segurança

| Pergunta do kit | Resposta |
|---|---|
| Quais dados são sensíveis? | Localização de cargas e veículos (risco de roubo), dados de clientes ligados ao `shipmentId` |
| Quem pode acessar? | Sensor: só envia leituras. Squads e operadores: consultas. Só o Fleet/operador vincula sensores |
| Como autenticar? | Sensor: header `X-Device-Key` (✅). **Squads: header `X-API-Key`, uma chave por squad** (✅, comparação em tempo constante). Usuários finais: JWT/OAuth2 (⏳) |
| Como autorizar? | Todo squad autenticado consulta; só WMS, Fleet e o próprio Track vinculam sensores (`POST /devices`, senão 403) (✅) |
| Como proteger as APIs? | Validação de entrada (Pydantic, ✅), HTTPS no gateway (⏳), rate limit (⏳), usuário sem root no container (✅) |

## Pipeline DevSecOps
- **Trivy:** dependências, segredos e Dockerfile (`fs`) + imagem final (`image`) no CI.
- **SonarQube/SonarCloud:** roda quando o secret `SONAR_TOKEN` está configurado.

## Chaves de API entre squads
- Configuradas em `SQUAD_API_KEYS` (`squad=chave,squad=chave`), geradas com `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- Entregues a cada squad por canal privado; trocar a chave de um squad não afeta os outros.
- Cada chamada conta em `track_chamadas_por_squad_total{squad}`, permitindo ver no Grafana quem usa a API.
- Detalhes para os outros squads: [contrato, seção 7](../contracts/CONTRATO_EVENTOS.md#7-chaves-de-api-entre-squads).

## Pontos de atenção
- As chaves `dev-*` de `SQUAD_API_KEYS` e o `DEVICE_API_KEY` padrão são só para desenvolvimento: troquem via variável de ambiente/secret.
- `config.h` do firmware (senha do Wi-Fi) está no `.gitignore`: **nunca** commitem.
- RabbitMQ com `guest/guest` só vale localmente.
