"""Metricas Prometheus (expostas em GET /metrics) para o dashboard Grafana."""
from prometheus_client import Counter, Gauge

leituras_total = Counter("track_leituras_total", "Leituras recebidas dos sensores", ["device_id"])
eventos_publicados_total = Counter("track_eventos_publicados_total", "Eventos publicados no RabbitMQ", ["evento"])
erros_publicacao_total = Counter("track_erros_publicacao_total", "Falhas ao publicar no RabbitMQ")
alertas_ativos = Gauge("track_alertas_ativos", "Alertas de condicao ativos")
temperatura = Gauge("track_temperatura_celsius", "Ultima temperatura lida", ["device_id", "shipment_id"])
umidade = Gauge("track_umidade_percent", "Ultima umidade lida", ["device_id", "shipment_id"])
dispositivos_online = Gauge("track_dispositivos_online", "Sensores enviando dentro do limite de offline")
