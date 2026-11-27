import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
# Convencao da plataforma (a mesma do WMS): um exchange topic por modulo produtor,
# routing key <modulo>.<evento.em.pontos>.v<versao> e uma fila <consumidor>.<produtor>.events com DLQ.
EXCHANGE = os.getenv("EXCHANGE", "siglog.tracking.events")
ROUTING_PREFIX = "tracking"
SOURCE = "tracking"
SERVICE_NAME = "siglog-track"

# Consumo dos eventos do WMS (fila criada em monitoring/rabbitmq/definitions.json)
CONSUMIR_WMS = os.getenv("CONSUMIR_WMS", "false").lower() == "true"
FILA_WMS = os.getenv("FILA_WMS", "tracking.wms.events")

DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "troque-esta-chave")
OFFLINE_SEGUNDOS = int(os.getenv("OFFLINE_SEGUNDOS", "60"))
HISTORICO_MAX_POR_CARGA = int(os.getenv("HISTORICO_MAX_POR_CARGA", "5000"))


def _ler_chaves(valor: str) -> dict[str, str]:
    """"fleet=abc,finance=def" -> {"abc": "fleet", "def": "finance"} (chave -> squad)."""
    chaves = {}
    for par in filter(None, (p.strip() for p in valor.split(","))):
        squad, _, chave = par.partition("=")
        if squad and chave:
            chaves[chave.strip()] = squad.strip().lower()
    return chaves


# Uma chave por squad que consome a API REST do Track. Em producao, defina via secret:
#   SQUAD_API_KEYS="wms=...,fleet=...,finance=...,crm=...,track=..."
SQUAD_API_KEYS = _ler_chaves(os.getenv(
    "SQUAD_API_KEYS",
    "wms=dev-wms,fleet=dev-fleet,finance=dev-finance,people=dev-people,crm=dev-crm,track=dev-track",
))

# Quais squads podem vincular sensores a cargas (POST /devices).
SQUADS_QUE_VINCULAM_DISPOSITIVOS = {"wms", "fleet", "track"}
