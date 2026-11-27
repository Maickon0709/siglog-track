"""Autenticacao entre squads: cada squad chama a API do Track com a propria chave (header X-API-Key)."""
from __future__ import annotations

import hmac

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from src.config import settings
from src.infrastructure import metricas

_chave_squad = APIKeyHeader(name="X-API-Key", auto_error=False,
                            description="Chave do squad que esta chamando (uma por squad)")


def squad_autenticado(chave: str | None = Security(_chave_squad)) -> str:
    """Devolve o nome do squad dono da chave ou responde 401."""
    if chave:
        for valida, squad in settings.SQUAD_API_KEYS.items():
            if hmac.compare_digest(chave, valida):
                metricas.chamadas_por_squad_total.labels(squad).inc()
                return squad
    raise HTTPException(401, "X-API-Key ausente ou invalida", headers={"WWW-Authenticate": "ApiKey"})


def exigir_squad(permitidos: set[str]):
    """Autoriza so os squads da lista (403 para os demais)."""
    def _verificar(squad: str = Security(squad_autenticado)) -> str:
        if squad not in permitidos:
            raise HTTPException(403, f"squad '{squad}' nao tem permissao para esta operacao")
        return squad
    return _verificar
