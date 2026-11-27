import os

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/%2F")
EXCHANGE = os.getenv("EXCHANGE", "siglog.events")
ROUTING_PREFIX = "tracking"
SERVICE_NAME = "siglog-track"

DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "troque-esta-chave")
OFFLINE_SEGUNDOS = int(os.getenv("OFFLINE_SEGUNDOS", "60"))
HISTORICO_MAX_POR_CARGA = int(os.getenv("HISTORICO_MAX_POR_CARGA", "5000"))
