# 03 — Personas, Matriz CSD e Mapa de Empatia

> ✏️ Validem estas personas com entrevistas reais (colegas, motoristas, farmacêuticos) e ajustem.

## Persona 1 — Carla, operadora da torre de controle
- 32 anos, monitora 40 caminhões por turno.
- **Objetivo:** saber na hora quando uma carga sai da temperatura.
- **Dor:** hoje só descobre o problema quando o cliente reclama na entrega.
- **Como o Track ajuda:** painel com alertas e o gráfico de temperatura ao vivo.

## Persona 2 — Rafael, gerente de qualidade de um laboratório (cliente)
- 45 anos, responde pela integridade das vacinas.
- **Objetivo:** comprovar que a carga ficou entre 2 e 8 °C durante toda a viagem.
- **Dor:** precisa de evidência para auditoria da ANVISA.
- **Como o Track ajuda:** histórico completo por carga e alertas com duração.

## Persona 3 — João, motorista
- 50 anos, usa o celular durante as paradas.
- **Objetivo:** ser avisado antes que a carga estrague.
- **Como o Track ajuda:** o Fleet recebe o `AlertaTemperatura` e avisa o motorista.

## Matriz CSD
| Certezas | Suposições | Dúvidas |
|---|---|---|
| Cargas sensíveis têm faixa de temperatura definida | 3 leituras seguidas evitam alarme falso | Qual o intervalo ideal entre leituras? |
| O sensor perde sinal em alguns trechos | O Finance usa a duração da violação para multar | O professor aceita GPS com posição fixa? |
| Outros squads dependem dos nossos eventos | A operadora prefere alerta a relatório | Quem vincula o sensor à carga: WMS ou Fleet? |

## Mapa de Empatia (Carla)
| Pensa e sente | Ouve | Vê | Fala e faz |
|---|---|---|---|
| Medo de perder uma carga cara | Reclamação de cliente | Muitas telas e planilhas | Liga para o motorista para conferir |
| **Dores:** descobre tarde, falta prova | | | **Ganhos:** alerta automático, histórico confiável |
