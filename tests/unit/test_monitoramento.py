"""Testes unitarios das regras de dominio."""
from datetime import datetime, timedelta, timezone

from src.domain.monitoramento import (
    FAIXAS_POR_TIPO,
    Dispositivo,
    Leitura,
    processar_leitura,
    verificar_offline,
)

T0 = datetime(2026, 11, 26, 14, 0, tzinfo=timezone.utc)


def novo_disp(tipo="VACINA"):
    return Dispositivo("IOT-001", "EXP-001", tipo, FAIXAS_POR_TIPO[tipo], "VEI-042", "VIA-1")


def ler(disp, temps, inicio=T0, passo=10, umidade=None):
    eventos = []
    for i, t in enumerate(temps):
        ts = inicio + timedelta(seconds=i * passo)
        eventos += processar_leitura(disp, Leitura(t, ts, umidade), ts)
    return eventos


def nomes(eventos):
    return [n for n, _ in eventos]


def test_leitura_normal_so_gera_temperatura_atualizada():
    ev = ler(novo_disp(), [5.0])
    assert nomes(ev) == ["TemperaturaAtualizada"]
    assert ev[0][1]["dentroDaFaixa"] is True
    assert ev[0][1]["vehicleId"] == "VEI-042"


def test_posicao_so_quando_ha_coordenadas():
    disp = novo_disp()
    ev = processar_leitura(disp, Leitura(5.0, T0, latitude=-23.5, longitude=-46.6), T0)
    assert nomes(ev) == ["TemperaturaAtualizada", "PosicaoAtualizada"]


def test_alerta_somente_apos_tres_leituras_seguidas():
    disp = novo_disp()
    assert "AlertaTemperatura" not in nomes(ler(disp, [9.0, 9.5]))
    ev = ler(disp, [9.4], inicio=T0 + timedelta(seconds=20))
    alerta = dict(ev)["AlertaTemperatura"]
    assert alerta["tipo"] == "TEMPERATURA_ALTA"
    assert alerta["inicioViolacao"] == "2026-11-26T14:00:00Z"
    assert alerta["severidade"] == "ALERTA"


def test_pico_isolado_nao_gera_alerta():
    assert "AlertaTemperatura" not in nomes(ler(novo_disp(), [9.0, 9.0, 5.0, 9.0, 9.0, 5.0]))


def test_alerta_emitido_uma_unica_vez():
    assert nomes(ler(novo_disp(), [9, 9, 9, 9, 9, 9])).count("AlertaTemperatura") == 1


def test_severidade_critica():
    alerta = dict(ler(novo_disp(), [11.0, 11.0, 11.0]))["AlertaTemperatura"]
    assert alerta["severidade"] == "CRITICA"


def test_encerramento_traz_duracao_e_valor_extremo():
    ev = ler(novo_disp(), [9.0, 12.0, 10.0, 5.0])
    fim = dict(ev)["AlertaTemperaturaEncerrado"]
    assert fim["duracaoSegundos"] == 30
    assert fim["valorExtremo"] == 12.0
    assert fim["alertId"] == dict(ev)["AlertaTemperatura"]["alertId"]


def test_temperatura_baixa():
    alerta = dict(ler(novo_disp(), [1.0, 0.5, 1.5]))["AlertaTemperatura"]
    assert alerta["tipo"] == "TEMPERATURA_BAIXA"
    assert alerta["limiteMin"] == 2.0


def test_umidade_alta():
    alerta = dict(ler(novo_disp("RESFRIADO"), [4, 4, 4], umidade=95))["AlertaTemperatura"]
    assert alerta["tipo"] == "UMIDADE_ALTA"
    assert alerta["limiteMax"] == 90.0


def test_offline_uma_vez_e_reseta_ao_voltar():
    disp = novo_disp()
    ler(disp, [5.0])
    assert verificar_offline(disp, T0 + timedelta(seconds=30), 60) is None
    nome, dados = verificar_offline(disp, T0 + timedelta(seconds=75), 60)
    assert nome == "DispositivoOffline" and dados["segundosSemSinal"] == 75
    assert verificar_offline(disp, T0 + timedelta(seconds=90), 60) is None
    ler(disp, [5.0], inicio=T0 + timedelta(seconds=100))
    assert disp.offline_notificado is False
