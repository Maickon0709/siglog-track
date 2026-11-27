# Estratégia Git (Encontro 7 — GitFlow)

## Branches
| Branch | Uso | Quem faz merge |
|---|---|---|
| `main` | Só versões entregues (Marco 1, Marco 2, RC, v1.0.0). Cada merge gera tag | Via PR de `release/*` ou `hotfix/*` |
| `develop` | Integração do que está pronto | Via PR de `feature/*` |
| `feature/<id>-<descricao>` | Uma história do backlog. Ex.: `feature/uc07-alerta-temperatura` | Sai de `develop` |
| `release/<versao>` | Congelamento antes de uma entrega. Ex.: `release/1.0.0` | Sai de `develop`, entra em `main` e `develop` |
| `hotfix/<descricao>` | Correção urgente em produção | Sai de `main`, entra em `main` e `develop` |

## Regras (Definition of Done do kit)
1. Ninguém faz push direto em `main` ou `develop`: proteger as duas branches no GitHub
   (*Settings → Branches → Add rule*: exigir PR, 1 aprovação e o CI passando).
2. Todo PR precisa de **code review** de outro integrante.
3. O CI (lint, testes, build, Trivy, docker build) precisa estar verde.
4. Commits no formato *Conventional Commits*: `feat:`, `fix:`, `docs:`, `test:`, `ci:`, `refactor:`.

## Versionamento
SemVer com tags: `v0.1.0` (Marco 1), `v0.2.0` (Marco 2), `v1.0.0-rc.1` (encontro 15), `v1.0.0` (Demoday).
Cada tag `v*` publica a imagem no GitHub Container Registry (`cd.yml`).
