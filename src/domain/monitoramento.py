"""Regras de dominio do monitoramento de condicao da carga.

Sem dependencias externas: recebe leituras e devolve eventos de dominio
(nome, dados). Quem publica no RabbitMQ e a camada de aplicacao.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

LEITURAS_PARA_ALERTA = 3
EXCESSO_CRITICO_TEMPERATURA = 2.0  # graus alem do limite
EXCESSO_CRITICO_UMIDADE = 10.0     # pontos percentuais alem do limite


@dataclass(frozen=True)
class Faixa:
    temp_min: float | None
    temp_max: float | None
    umidade_max: float | None = None


# Faixas padrao por tipo de carga. POST /devices pode sobrescrever.
FAIXAS_POR_TIPO: dict[str, Faixa] = {
    "VACINA": Faixa(2.0, 8.0),
    "RESFRIADO": Faixa(0.0, 7.0, 90.0),
    "CONGELADO": Faixa(None, -18.0),
    "AMBIENTE": Faixa(15.0, 30.0, 70.0),
}


@dataclass
class Violacao:
    alert_id: str
    tipo: str
    inicio: datetime
    valor_extremo: float


@dataclass
class Dispositivo:
    device_id: str
    shipment_id: str
    tipo_carga: str
    faixa: Faixa
    vehicle_id: str | None = None
    trip_id: str | None = None
    ultima_leitura: datetime | None = None
    ultima_recepcao: datetime | None = None  # relogio do servidor, para offline
    offline_notificado: bool = False
    # por tipo de violacao: leituras seguidas fora da faixa e alerta ativo
    fora_seguidas: dict[str, int] = field(default_factory=dict)
    primeira_fora: dict[str, datetime] = field(default_factory=dict)
    extremo_fora: dict[str, float] = field(default_factory=dict)
    ativas: dict[str, Violacao] = field(default_factory=dict)

    def vinculo(self) -> dict:
        return {
            "deviceId": self.device_id,
            "shipmentId": self.shipment_id,
            "vehicleId": self.vehicle_id,
            "tripId": self.trip_id,
        }


@dataclass(frozen=True)
class Leitura:
    temperatura: float
    timestamp: datetime
    umidade: float | None = None
    bateria: int | None = None
    latitude: float | None = None
    longitude: float | None = None


Evento = tuple[str, dict]


def _iso(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _verificacoes(faixa: Faixa, leitura: Leitura) -> dict[str, tuple[bool, float, float | None]]:
    """tipo -> (fora_da_faixa, valor, limite)."""
    t = leitura.temperatura
    checks: dict[str, tuple[bool, float, float | None]] = {}
    if faixa.temp_max is not None:
        checks["TEMPERATURA_ALTA"] = (t > faixa.temp_max, t, faixa.temp_max)
    if faixa.temp_min is not None:
        checks["TEMPERATURA_BAIXA"] = (t < faixa.temp_min, t, faixa.temp_min)
    if faixa.umidade_max is not None and leitura.umidade is not None:
        u = leitura.umidade
        checks["UMIDADE_ALTA"] = (u > faixa.umidade_max, u, faixa.umidade_max)
    return checks


def _severidade(tipo: str, valor: float, limite: float) -> str:
    excesso = abs(valor - limite)
    critico = EXCESSO_CRITICO_UMIDADE if tipo == "UMIDADE_ALTA" else EXCESSO_CRITICO_TEMPERATURA
    return "CRITICA" if excesso > critico else "ALERTA"


def _mais_extremo(tipo: str, atual: float, novo: float) -> float:
    return min(atual, novo) if tipo == "TEMPERATURA_BAIXA" else max(atual, novo)


def processar_leitura(disp: Dispositivo, leitura: Leitura, recebida_em: datetime) -> list[Evento]:
    """Atualiza o estado do dispositivo e devolve os eventos gerados."""
    disp.ultima_leitura = leitura.timestamp
    disp.ultima_recepcao = recebida_em
    disp.offline_notificado = False

    checks = _verificacoes(disp.faixa, leitura)
    temp_ok = not any(fora for tipo, (fora, _, _) in checks.items() if tipo.startswith("TEMPERATURA"))

    eventos: list[Evento] = [(
        "TemperaturaAtualizada",
        {
            **disp.vinculo(),
            "temperatura": leitura.temperatura,
            "umidade": leitura.umidade,
            "bateria": leitura.bateria,
            "dentroDaFaixa": temp_ok,
        },
    )]

    if leitura.latitude is not None and leitura.longitude is not None:
        eventos.append((
            "PosicaoAtualizada",
            {**disp.vinculo(), "latitude": leitura.latitude, "longitude": leitura.longitude},
        ))

    for tipo, (fora, valor, limite) in checks.items():
        ativa = disp.ativas.get(tipo)
        if fora:
            if disp.fora_seguidas.get(tipo, 0) == 0:
                disp.primeira_fora[tipo] = leitura.timestamp
                disp.extremo_fora[tipo] = valor
            disp.fora_seguidas[tipo] = disp.fora_seguidas.get(tipo, 0) + 1
            disp.extremo_fora[tipo] = _mais_extremo(tipo, disp.extremo_fora[tipo], valor)
            if ativa:
                ativa.valor_extremo = disp.extremo_fora[tipo]
            elif disp.fora_seguidas[tipo] >= LEITURAS_PARA_ALERTA:
                ativa = Violacao(
                    alert_id=f"ALT-{uuid.uuid4().hex[:6]}",
                    tipo=tipo,
                    inicio=disp.primeira_fora[tipo],
                    valor_extremo=disp.extremo_fora[tipo],
                )
                disp.ativas[tipo] = ativa
                eventos.append((
                    "AlertaTemperatura",
                    {
                        "alertId": ativa.alert_id,
                        **disp.vinculo(),
                        "tipo": tipo,
                        "valor": valor,
                        "limiteMin": disp.faixa.temp_min if tipo != "UMIDADE_ALTA" else None,
                        "limiteMax": disp.faixa.umidade_max if tipo == "UMIDADE_ALTA" else disp.faixa.temp_max,
                        "tipoCarga": disp.tipo_carga,
                        "severidade": _severidade(tipo, valor, limite),
                        "inicioViolacao": _iso(ativa.inicio),
                    },
                ))
        else:
            disp.fora_seguidas[tipo] = 0
            if ativa:
                del disp.ativas[tipo]
                eventos.append((
                    "AlertaTemperaturaEncerrado",
                    {
                        "alertId": ativa.alert_id,
                        **disp.vinculo(),
                        "tipo": tipo,
                        "valorExtremo": ativa.valor_extremo,
                        "inicioViolacao": _iso(ativa.inicio),
                        "fimViolacao": _iso(leitura.timestamp),
                        "duracaoSegundos": int((leitura.timestamp - ativa.inicio).total_seconds()),
                    },
                ))

    return eventos


def verificar_offline(disp: Dispositivo, agora: datetime, limite_segundos: int) -> Evento | None:
    """Gera DispositivoOffline uma unica vez ate o sensor voltar a enviar."""
    if disp.ultima_recepcao is None or disp.offline_notificado:
        return None
    sem_sinal = int((agora - disp.ultima_recepcao).total_seconds())
    if sem_sinal <= limite_segundos:
        return None
    disp.offline_notificado = True
    return (
        "DispositivoOffline",
        {
            **disp.vinculo(),
            "ultimaLeitura": _iso(disp.ultima_leitura or disp.ultima_recepcao),
            "segundosSemSinal": sem_sinal,
        },
    )
