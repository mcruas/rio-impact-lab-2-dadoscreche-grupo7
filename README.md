# Solução — Rio Impact Lab 2026 | Grupo 7

Este repositório é a solução deste grupo para o desafio de dados de Inscrição Creche do Rio de Janeiro, do Claude Impact Lab 2026.

- O enunciado, o briefing, a apresentação e as bases de dados originais do desafio (padrão para todos os grupos) estão em [`desafio/`](desafio/README.md).
- A análise exploratória do grupo (hipóteses e resultados) está em [`eda/`](eda/HIPOTESES_EDA.md) — ver também os [resultados de H6 e H12](eda/RESULTADOS_H6_H12.md) e a [reconciliação com o diagnóstico e o motor de matching](eda/RESULTADOS_MATCHING.md).
- O diagnóstico do problema (P1-P6: o que os dados mostram, causa, solução proposta) está em [`PROBLEMAS.md`](PROBLEMAS.md).
- A solução está sendo construída em [`modulos/`](modulos/), um componente por integrante, com contratos entre eles definidos em [`contracts/`](contracts/README.md). Ver [`ARQUITETURA.md`](ARQUITETURA.md) para a visão geral antes de começar, e [`INTEGRACAO_RMI_WHATSAPP.md`](INTEGRACAO_RMI_WHATSAPP.md) para como os módulos `documentacao` e `acompanhamento` se apoiariam na infraestrutura que a Prefeitura já opera em produção.
- Especificação, implementação e backtest do motor de match (Eixo 2) estão em [`modulos/match-engine/MATCHING.md`](modulos/match-engine/MATCHING.md).
