# Hipóteses para EDA — Eficiência do Processo de Alocação de Creches

> Documento de planejamento. As hipóteses abaixo se apoiam nos fatos já confirmados no dicionário de dados (`../desafio/README.md`, `../desafio/Bases IC_ ClassificadoseFila/README_dicionario_dados.md`) e servem para priorizar o que vale a pena investigar com código antes de investir tempo.
>
> **H6 e H12 já foram investigadas com dados reais** — ver [`RESULTADOS_H6_H12.md`](RESULTADOS_H6_H12.md) e o script [`investigar_h6_h12.py`](investigar_h6_h12.py).

## 1. Objetivo e definição operacional de "eficiência de alocação"

A pergunta motivadora é: **como aumentar a eficiência do processo que aloca crianças a vagas de creche?** Antes de medir eficiência, precisamos de KPIs candidatos — a validar/calcular numa etapa futura:

- **Taxa de atendimento efetivo**: % de crianças (`aluno_anon` distintos) com pelo menos uma opção em situação `Confirmado`, `Ativo` ou `Selecionado`/`Selecionado da lista`, sobre o total de crianças inscritas no ano.
- **Posição média da opção atendida**: quando há confirmação, em que ordem de preferência (`opcao` = 1ª, 2ª...) ela ocorre — mede o quão bem o sistema respeita a preferência da família.
- **Taxa de esvaziamento da lista de espera**: das inscrições que entram em `Lista de espera`, quantas migram para `Selecionado da lista` dentro do mesmo processo.
- **Taxa de perda total**: % de crianças cujas *todas* as opções terminam em algum tipo de cancelamento (nenhuma confirmação em nenhuma opção).
- **Equidade territorial de atendimento**: taxa de atendimento efetivo, quebrada por bairro/microárea — mede se a eficiência é uniforme no território ou concentrada em certas regiões.
- **Utilização da oferta**: vagas ofertadas (`OferecimentosEvagas`) vs. vagas efetivamente preenchidas por unidade/ano — mede desperdício de capacidade.

Essas métricas fundamentam os três eixos abaixo.

## 2. Eixo 1 — Descasamento oferta x demanda territorial

**Fontes**: Query A (`bairro`/`CEP` do responsável, `unidade`/`nome_unidade` escolhida), Query D (`esc_codigo`, `bairro`, `cep` da unidade), `OferecimentosEvagas/` (vagas ofertadas por unidade/ano, parceiras e públicas), `Microáreas_SME_revisãoIPP/` (território), `NascidosvivosRJ.xlsx` (proxy de demanda futura).

- **H1**: Existe descasamento espacial relevante entre o bairro de residência da família e o bairro da unidade nas opções escolhidas — famílias estão sendo obrigadas a escolher/são alocadas em creches longe de casa por falta de vaga próxima?
- **H2**: Bairros/microáreas com alta concentração de `Lista de espera` e `Cancelado pelo sistema` coincidem com regiões de alta natalidade (nascidos vivos, com defasagem de ~1-3 anos até a idade de creche) e baixa oferta de vagas — ou seja, a escassez é territorialmente concentrada, não uniforme?
- **H3**: A evolução da oferta de vagas (parceiras + públicas, 2021-2025) acompanha a evolução da natalidade por região, ou a rede está sendo expandida/contraída de forma desalinhada com a demanda futura?
- **H4**: Há unidades públicas com baixa taxa de ocupação convivendo, na mesma região, com unidades parceiras com fila de espera longa — sinal de ineficiência de alocação entre tipos de rede, não apenas de escassez agregada?
- **H5**: O bairro/CEP nulo em 2,8% das inscrições da Query A tem padrão de concentração (por ano, por região, por situação) que possa enviesar qualquer análise territorial se ignorado?

## 3. Eixo 2 — Atrito e cancelamentos no funil de inscrição

**Fontes**: Query A (`situacao`, `data_criacao`, `opcao`, `ano`, `aluno_anon`).

- **H6**: A situação `Cancelado pelo sistema` (39% das linhas) está concentrada em quais posições de opção (1ª vs. 2ª vs. 3ª+)? É plausível que seja um cancelamento automático por não-confirmação — quantas dessas crianças acabam `Confirmado` em *outra* opção da mesma inscrição, versus saem do processo sem nenhuma confirmação?
- **H7**: Qual a taxa real de crianças (`aluno_anon` distintos) sem nenhuma opção confirmada em todas as suas linhas — a "perda total" do funil — e como essa taxa varia por ano e por região?
- **H8**: `data_criacao` mostra sazonalidade de inscrições (picos em determinados meses/períodos) que possa estar sobrecarregando o sistema e gerando mais cancelamentos automáticos por prazo?
- **H9**: A taxa de cancelamento pelo sistema mudou ao longo dos 5 processos (2021→2025) — piorou, melhorou ou ficou estável? Pode indicar mudanças de processo, capacidade ou regras entre os anos.
- **H10**: As ~34.486 crianças (13,3%) que reaparecem em mais de um ano — elas tendem a repetir desfechos ruins (fila/cancelamento recorrente, sinalizando falha crônica de atendimento) ou o reaparecimento reflete simplesmente mudança de preferência/endereço?
- **H11**: Existe correlação entre número de opções escolhidas por inscrição (1 a 6) e a chance de confirmação — se sim, orientar famílias a preencher mais opções seria uma alavanca de eficiência de baixo custo?

## 4. Eixo 3 — Efetividade dos critérios de classificação/pontuação

**Fontes**: Query B (`resposta`, `confirmado` por pergunta), Query C (`perg_pontuacao`, `perg_criterio`, `perg_id`, mapeamento por ano via `ich_perg_id`), Query A (`situacao` como desfecho).

- **H12**: A pontuação total por inscrição (soma dos pontos das perguntas respondidas `Sim` e `confirmado = Sim`) prediz de forma consistente o desfecho observado (`Confirmado` > `Lista de espera` > `Cancelado`)? Isto é, a fila resultante realmente segue a régua de pontuação, ou há muito desvio?
- **H13**: A reforma de 2024 (13→3 perguntas sobreviventes; peso da pergunta sobre deficiência da criança, `perg_id = 2`, caindo de 100 para 25 pontos) teve efeito mensurável na proporção de crianças com deficiência que conseguem confirmação, comparando antes (2021-2023) e depois (2024-2025)?
- **H14**: Quantas inscrições empatam em pontuação total e dependem dos critérios de desempate (`perg_criterio = Sim`, `perg_pontuacao = 0`) para definir a posição na fila — os critérios de desempate atuais são suficientes ou geram desempates arbitrários (ex.: por ordem de inscrição)?
- **H15**: Há divergência sistemática entre `resposta` (9,4% `Sim`) e `confirmado` (12,4% `Sim`) — ou seja, respostas não declaradas mas confirmadas por outra via, ou declaradas e não confirmadas? Essa divergência afeta de forma desproporcional algum grupo/critério específico?
- **H16**: A distribuição de pontos entre as perguntas é concentrada em poucos critérios de peso alto — existe uma pergunta que praticamente decide sozinha a posição na fila, reduzindo o poder discriminativo dos demais critérios socioeconômicos?

## 5. Fontes e junções necessárias por eixo

| Eixo | Arquivos envolvidos | Chaves de junção |
| --- | --- | --- |
| 1 — Território | Query A, Query D, `OferecimentosEvagas/*`, `Microáreas_SME_revisãoIPP/*`, `NascidosvivosRJ.xlsx` | `unidade` (A) = `esc_codigo` (D); bairro/CEP como chave geográfica aproximada com as demais bases (sem chave exata — exige normalização de nomes de bairro) |
| 2 — Funil | Query A apenas | `aluno_anon` para agregar por criança; `(prm_id, plm_id, ipl_id)` para agregar por inscrição |
| 3 — Classificação | Query B, Query C, Query A | `(prm_id, plm_id, ipl_id)` entre A e B; `ich_perg_id` entre B e C; `perg_id` para comparar a mesma pergunta entre anos |

## 6. Cuidados e limitações

- **Anonimização**: indicadores absolutos não representam a realidade (dados passaram por aleatorização/generalização/supressão) — qualquer conclusão deve ser enquadrada como ilustrativa da dinâmica, não como número oficial.
- **Quebra de régua 2023→2024**: comparações de pontuação/critérios entre períodos exigem tratar 2021-2023 e 2024-2025 como dois regimes distintos, nunca somar/comparar pontuação bruta diretamente entre eles (ver H13).
- **Query A não tem capacidade/vaga como denominador nativo**: ela é só o lado da demanda (inscrições). Para calcular taxas de ocupação/utilização de oferta (H2-H4), é obrigatório cruzar com `OferecimentosEvagas/`, que tem periodicidade e fonte diferentes (mensal, com defasagem de ~1 mês, `LEIAME_OFERECIMENTOSPARCEIRASEPUBLICAS.txt`) — os dois lados não são diretamente comparáveis sem ajuste de granularidade temporal.
- **Nulos geográficos**: 2,8% de bairro/CEP nulos em Query A podem enviesar qualquer corte territorial se não forem tratados explicitamente (excluir vs. imputar).
- **`04_UnidadesEscolaresComEndereco.csv` sem header** e **`02_QueryB` não cabe no Excel/memória sem leitura em blocos** — cuidados técnicos de leitura, não analíticos, mas que podem gerar erro silencioso de amostragem se ignorados.
- **Junção geográfica com `OferecimentosEvagas`/`Microáreas`/`NascidosvivosRJ`** provavelmente não tem chave exata (não há `esc_codigo` compartilhado confirmado) — exige checar essas planilhas para entender granularidade e normalizar nomes de bairro/unidade antes de qualquer join.

## 7. Próximos passos sugeridos (ordem de prioridade)

1. **Eixo 2 (funil)** — mais rápido de validar: usa só Query A, sem joins externos, e várias hipóteses (H6, H7, H9) são agregações diretas de `situacao`/`opcao`/`ano`. Bom ponto de partida para gerar o primeiro insight concreto.
2. **Eixo 3 (classificação)** — exige juntar A+B+C, mas ainda dentro do mesmo dataset (`Bases IC_ ClassificadoseFila/`), sem depender de normalização geográfica. H12 e H13 são as hipóteses com maior potencial de virar recomendação de política (ex.: revisar a régua de pontuação).
3. **Eixo 1 (território)** — mais custoso: exige inspecionar a estrutura real de `OferecimentosEvagas/`, `Microáreas_SME_revisãoIPP/` (shapefile) e `NascidosvivosRJ.xlsx` antes de tentar qualquer join, já que não há confirmação de chave exata entre essas bases e a Query A/D. Recomenda-se uma etapa exploratória só para mapear essas chaves antes de testar H1-H5.

Sugestão: validar este documento com o grupo, decidir por quais 2-3 hipóteses começar, e só então escrever os scripts de extração (Python/DuckDB, dado o volume de Query B) que gerem os números para confirmar ou refutar cada uma.
