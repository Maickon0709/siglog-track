"""Simula o ESP32 (mesmo JSON, mesmo endpoint) para testar sem o hardware.

Uso:
    python scripts/simular_sensor.py                # temperatura normal
    python scripts/simular_sensor.py --falha        # sobe a temperatura e depois normaliza
    python scripts/simular_sensor.py --url http://localhost:8000 --device IOT-002
So usa a biblioteca padrao do Python.
"""
import argparse
import json
import random
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def post(url, corpo, chave=None, chave_squad=None):
    headers = {"Content-Type": "application/json"}
    if chave:
        headers["X-Device-Key"] = chave
    if chave_squad:
        headers["X-API-Key"] = chave_squad
    req = urllib.request.Request(url, json.dumps(corpo).encode(), headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--chave", default="troque-esta-chave", help="X-Device-Key do sensor")
    p.add_argument("--chave-squad", default="dev-track", help="X-API-Key usada no POST /devices")
    p.add_argument("--device", default="IOT-001")
    p.add_argument("--shipment", default="EXP-001")
    p.add_argument("--intervalo", type=float, default=2.0)
    p.add_argument("--falha", action="store_true", help="simula quebra da cadeia fria")
    a = p.parse_args()

    print(post(f"{a.url}/devices", {"deviceId": a.device, "shipmentId": a.shipment,
                                    "vehicleId": "VEI-042", "tripId": "VIA-2026-0917",
                                    "tipoCarga": "VACINA"}, chave_squad=a.chave_squad))

    lat, lon, i = -23.5505, -46.6333, 0
    while True:
        base = 5.0
        if a.falha and 5 <= i % 20 < 12:
            base = 10.5  # fora da faixa 2-8 °C por 7 leituras
        lat += 0.0005
        lon += 0.0004
        corpo = {
            "deviceId": a.device,
            "temperatura": round(base + random.uniform(-0.4, 0.4), 2),
            "umidade": round(60 + random.uniform(-3, 3), 1),
            "bateria": max(0, 100 - i // 10),
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        status, resp = post(f"{a.url}/sensor-readings", corpo, a.chave)
        print(status, corpo["temperatura"], resp)
        i += 1
        time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
