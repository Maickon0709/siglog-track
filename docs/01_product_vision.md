# 01 — Visão do Produto

## Declaração de visão
**Para** operadores logísticos e clientes que transportam cargas sensíveis (vacinas, alimentos resfriados e congelados),
**que** precisam saber onde a carga está e se ela continua dentro das condições adequadas,
**o SIG-Log Track** é um serviço de rastreamento e telemetria IoT
**que** recebe dados de sensores físicos em tempo real, detecta quebras na cadeia fria e avisa os outros módulos da plataforma,
**diferente de** planilhas e registradores de temperatura lidos só na chegada,
**nosso produto** detecta o problema durante a viagem, a tempo de agir.

## Perguntas que o produto responde
1. **Onde está a carga?** (posição atual e histórico)
2. **A carga está dentro das condições adequadas?** (temperatura, umidade, bateria do sensor)

## Objetivos
| Objetivo | Indicador |
|---|---|
| Detectar violação de temperatura rapidamente | Alerta publicado em até 30 s (3 leituras de 10 s) |
| Evitar alarme falso | Pico isolado não gera alerta |
| Integrar a plataforma | Fleet, Finance e CRM consomem os eventos sem acoplamento de código |
| Ser observável | Logs, métricas e traces de cada leitura |

## Escopo
**Dentro:** cadastro de dispositivos, recepção de telemetria, detecção de anomalias (temperatura, umidade, dispositivo offline, fora de rota), alertas, histórico e consultas.
**Fora:** roteirização (Fleet), cobrança de multas e indenizações (Finance), notificação ao cliente final (CRM).

## Project Charter
| Item | Conteúdo |
|---|---|
| Squad | 03 — SIG-Log Track |
| Integrantes | ✏️ A PREENCHER (nome — papel: PO, Scrum Master, Dev, DevOps, QA) |
| Patrocinador | Professor da disciplina de Análise de Sistemas II |
| Prazo | Encontro 16 (Demoday) — Release v1.0.0 |
| Principais riscos | Hardware atrasar, integração com outros squads sem contrato fechado, rede Wi-Fi instável na apresentação |
| Mitigação | Simulador de sensor com o mesmo payload, contrato publicado cedo, roteador/celular próprio para a demo |
