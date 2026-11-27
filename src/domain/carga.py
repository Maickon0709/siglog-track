"""Status da carga no Track (UC09), alimentado pelos eventos de outros modulos."""
from __future__ import annotations

from dataclasses import dataclass, field

AGUARDANDO_EXPEDICAO = "AGUARDANDO_EXPEDICAO"
EM_TRANSITO = "EM_TRANSITO"


class EventoInvalido(ValueError):
    pass


@dataclass
class Carga:
    shipment_id: str
    status: str = AGUARDANDO_EXPEDICAO
    destino: str | None = None
    pedidos: list[str] = field(default_factory=list)
    expedida_em: str | None = None

    def para_dict(self) -> dict:
        return {"shipmentId": self.shipment_id, "status": self.status, "destination": self.destino,
                "orderIds": self.pedidos, "expedidaEm": self.expedida_em}


def aplicar_carga_expedida(carga: Carga | None, evento: dict) -> Carga:
    """CargaExpedida (WMS) -> a carga passa a EM_TRANSITO."""
    try:
        shipment_id = evento["shipmentId"]
        expedida_em = evento["timestamp"]
    except KeyError as faltando:
        raise EventoInvalido(f"CargaExpedida sem o campo {faltando}") from None
    carga = carga or Carga(shipment_id)
    carga.status = EM_TRANSITO
    carga.destino = evento.get("destination")
    carga.pedidos = list(evento.get("orderIds") or [])
    carga.expedida_em = expedida_em
    return carga
