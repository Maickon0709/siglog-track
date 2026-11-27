"""Gera contracts/openapi.yaml a partir da API. Rode depois de mudar qualquer rota:
    python -m scripts.exportar_openapi
"""
from pathlib import Path

import yaml

from src.api.main import criar_app

destino = Path(__file__).parents[1] / "contracts" / "openapi.yaml"
spec = criar_app(iniciar_monitor=False).openapi()
destino.write_text(yaml.safe_dump(spec, allow_unicode=True, sort_keys=False))
print(f"OpenAPI salvo em {destino}")
