// Teste de carga do SIG-Log Track. Uso: k6 run -e CENARIO=normal|pico|extremo scripts/load/k6_sensor.js
import http from "k6/http";
import { check } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const CHAVE = __ENV.DEVICE_API_KEY || "troque-esta-chave";
const CHAVE_SQUAD = __ENV.SQUAD_API_KEY || "dev-track";
const SENSORES = 50;

const CENARIOS = {
  normal: { rate: 100, duration: "2m" },
  pico: { rate: 500, duration: "2m" },
  extremo: { rate: 1000, duration: "1m" },
};
const c = CENARIOS[__ENV.CENARIO || "normal"];

export const options = {
  scenarios: {
    leituras: {
      executor: "constant-arrival-rate",
      rate: c.rate,
      timeUnit: "1s",
      duration: c.duration,
      preAllocatedVUs: 50,
      maxVUs: 500,
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
  },
  summaryTrendStats: ["avg", "p(95)", "p(99)", "max"],
};

const json = { headers: { "Content-Type": "application/json", "X-Device-Key": CHAVE } };

export function setup() {
  for (let i = 0; i < SENSORES; i++) {
    http.post(`${BASE}/devices`, JSON.stringify({
      deviceId: `LOAD-${i}`, shipmentId: `EXP-LOAD-${i}`, tipoCarga: "VACINA",
    }), { headers: { "Content-Type": "application/json", "X-API-Key": CHAVE_SQUAD } });
  }
}

export default function () {
  const i = Math.floor(Math.random() * SENSORES);
  const r = http.post(`${BASE}/sensor-readings`, JSON.stringify({
    deviceId: `LOAD-${i}`,
    temperatura: 5 + Math.random() * 2,
    umidade: 60,
    bateria: 90,
    latitude: -8.05 + Math.random() / 100,
    longitude: -34.9 + Math.random() / 100,
  }), json);
  check(r, { "202": (res) => res.status === 202 });
}
