# Resultados — H6 (funil/cancelamentos) e H12 (efetividade da pontuação)

> Gerado a partir de [`investigar_h6_h12.py`](investigar_h6_h12.py) (DuckDB lendo os `.csv.gz` diretamente, sem alterar os arquivos originais). Reexecute o script para reproduzir todos os números abaixo. Ver hipóteses originais em [`HIPOTESES_EDA.md`](HIPOTESES_EDA.md).

## Resumo executivo

- **20,6% das inscrições (70.566 de 343.308) somem do processo sem nunca terem sido atendidas nem terem passado pela lista de espera** — a "perda silenciosa" do funil, o número mais acionável para eficiência de alocação.
- **"Cancelado pelo sistema" é, na maioria das vezes, inofensivo**: 76,4% de quem recebe esse rótulo em alguma opção acaba atendido em outra opção da mesma inscrição. Só 23,6% (34.359 inscrições) de fato perdem tudo.
- **Escolher mais opções não aumenta a chance de ser atendido** (fica entre 54% e 58% de 1 a 5 opções) — refuta a hipótese H11 de que orientar famílias a marcar mais opções seria uma alavanca de eficiência.
- **A pontuação de classificação (H12) só é comparável entre anos depois de duas correções**: (1) usar `resposta='Sim' AND confirmado='Sim'`, não `confirmado='Sim'` isolado; (2) tratar 2021 separadamente — a taxa de `confirmado='Sim'` dado `resposta='Sim'` cai de 88,9% em 2021 para ~8% de 2022 em diante, uma quebra de definição/processo tão relevante quanto a já documentada mudança de régua 2023→2024.
- Feita a correção, **2022-2025 confirmam H12 na direção esperada**: quem foi atendido tem, em todo ano, a maior proporção de inscrições com pontuação válida positiva. Mas o que discrimina o desfecho é sobretudo **ter algum critério pontuado validado, não o valor exato da pontuação** — achado relevante para repensar o desenho da régua.
- Encontrados e corrigidos **dois problemas de qualidade de dado que, se ignorados, inviabilizariam essas análises**: CEP/bairro usam a string literal `"NULL"` como ausência (não nulo de verdade), e ~696 códigos de `aluno_anon` são "baldes" de crianças não identificáveis agrupadas sob o mesmo código, não uma criança real.

---

## 1. Qualidade de dado — achados e correções aplicadas

| # | Achado | Evidência | Correção aplicada |
| --- | --- | --- | --- |
| 1 | **Chaves primárias de A e B não têm duplicidade** | `(prm_id,plm_id,ipl_id,opcao)` em A e `(prm_id,plm_id,ipl_id,ich_perg_id)` em B: 0 grupos duplicados | Nenhuma necessária — chave confiável |
| 2 | **`situacao`, `opcao`, `ano` batem exatamente com o dicionário** | 8 valores de `situacao` nas mesmas contagens documentadas; `opcao` 1-6 sem outliers; `ano` só 2021-2025 | Nenhuma necessária |
| 3 | **CEP/bairro codificam ausência como a string `"NULL"`, não NULL real** | `CEP IS NULL` → 0 linhas; `CEP = 'NULL'` → 23.617 linhas (bate com o dicionário). Sem a correção, `"NULL"` aparece como se fosse um 5º bairro mais frequente do Rio | `NULLIF(CEP,'NULL')` / `NULLIF(bairro,'NULL')` antes de qualquer contagem ou join territorial |
| 4 | **`aluno_anon` tem códigos "balde" que juntam crianças distintas** | 696 códigos com mais de uma `nascimento_aluno_anomes` distinta sob o mesmo `aluno_anon` (3.465 linhas, 0,4% de A). Ex.: `aluno_0000003` aparece 192 vezes, ligado a 43 datas de nascimento e 141 responsáveis diferentes — não é uma criança com 192 inscrições, é um código de fallback da anonimização (provavelmente para registros sem CPF/DNV/NIS/nome suficientes para gerar uma chave própria) | Excluídos de qualquer análise por criança (H6.7, H6.8) |
| 5 | **4 linhas do processo 2024 têm `data_criacao` registrada em 2026** | Fora da janela esperada (processo fechado, extração deveria ir só até o ano do processo) | Volume desprezível (0,0005%); sinalizado, não afeta os números abaixo, mas filtrar se algum dia for feita análise de sazonalidade (H8) |
| 6 | **Taxa de `confirmado='Sim'` dado `resposta='Sim'` despenca de 88,9% (2021) para 7,9%-10,8% (2022-2025)** | Ver tabela na seção H12 | Tratar 2021 como regime à parte em qualquer comparação de score entre anos; a régua de pontuação (2023→2024) não é a única quebra temporal relevante nesta base |

Checagens que **não** encontraram problema (vale registrar, para não serem refeitas à toa): nenhuma inscrição excede a pontuação máxima teórica do seu ano; `perg_criterio='Sim'` sempre tem `perg_pontuacao=0`; nenhuma linha órfã além das 221 já documentadas entre B e A; nenhuma pergunta duplicada em `(ano, ich_perg_id)` na Query C.

---

## 2. H6 — Atrito e cancelamentos no funil

### 2.1 Funil geral (nível inscrição, `n=343.308`)

| Desfecho | Inscrições | % |
| --- | ---: | ---: |
| Atendida (Confirmado/Ativo/Selecionado/Selecionado da lista) | 194.434 | 56,6% |
| Fila (só Lista de espera, nunca atendida) | 78.308 | 22,8% |
| **Cancelada — sem atendimento e sem nunca ter passado pela fila** | **70.566** | **20,6%** |

Esse último grupo (20,6%) é o alvo mais direto para "aumentar a eficiência de alocação": são famílias que nunca chegaram sequer a esperar numa fila — saíram do processo diretamente.

### 2.2 "Cancelado pelo sistema" é majoritariamente benigno

Das inscrições que tiveram pelo menos uma opção com `situacao = 'Cancelado pelo sistema'`:

| Desfecho final da inscrição | n | % |
| --- | ---: | ---: |
| Atendida em outra opção da mesma inscrição | 111.048 | 76,4% |
| Perda total | 34.359 | 23,6% |
| Ficou em fila | 19 | 0,0% |

Interpretação: o rótulo "Cancelado pelo sistema" concentra 39% de todas as linhas da Query A, mas na maior parte dos casos ele é apenas o sistema fechando automaticamente as opções concorrentes de uma família que já foi atendida em outra — **não é, por si, um sinal de falha**. O problema real e quantificável é o subconjunto de 34.359 inscrições/ano (23,6% desse grupo) que não têm nenhuma opção atendida.

### 2.3 Tendência ao longo dos 5 anos

| Ano | % Cancelado pelo sistema |
| --- | ---: |
| 2021 | 36,3% |
| 2022 | 36,2% |
| 2023 | 33,9% |
| 2024 | 42,9% |
| 2025 | 44,1% |

Piora visível a partir de 2024 — coincide com a reforma da régua de pontuação (menos perguntas, pesos menores) e merece investigação de causa (mudança de regra do processo? maior volume de inscrições por família? mudança de capacidade?).

### 2.4 Número de opções escolhidas não muda a chance de atendimento (refuta H11)

| Nº opções | Inscrições | % atendida |
| --- | ---: | ---: |
| 1 | 132.891 | 57,9% |
| 2 | 68.152 | 54,4% |
| 3 | 56.704 | 56,2% |
| 4 | 29.938 | 54,9% |
| 5 | 55.618 | 57,7% |

A taxa de atendimento fica estável entre 54% e 58% independentemente de quantas opções a família marca. **Orientar famílias a escolherem mais opções não é, isoladamente, uma alavanca de eficiência** — o gargalo está em outro lugar (oferta territorial, prioridade da fila, etc.).

### 2.5 Reincidência de crianças (após excluir os códigos "balde")

- A grande maioria das crianças (256.684) tem só 1 inscrição no ano; casos com várias inscrições no mesmo ano existem mas são raros e pequenos em volume (até 12, isoladamente).
- 32.455 crianças reaparecem em mais de 1 dos 5 anos do processo — coerente com o percentual documentado (13,3%) uma vez removidos os códigos-balde.

---

## 3. H12 — A pontuação de classificação prediz o desfecho?

### 3.1 Correção necessária na fórmula de score

A pontuação de uma pergunta só deveria contar quando a família **declarou "Sim" E a resposta foi validada** (`confirmado='Sim'`). Usar apenas `confirmado='Sim'` (sem checar `resposta`) infla o score, porque `confirmado` também aparece em 472.047 linhas onde a resposta foi **"Não"** — ali, "confirmado" provavelmente significa "a resposta 'Não' foi validada como correta", não "a família tem direito ao ponto". Score corrigido usado a partir daqui: `SUM(perg_pontuacao) WHERE resposta='Sim' AND confirmado='Sim'`.

### 3.2 2021 não é comparável aos demais anos

| Ano | % confirmado='Sim' dado resposta='Sim' |
| --- | ---: |
| 2021 | 88,9% |
| 2022 | 10,8% |
| 2023 | 8,7% |
| 2024 | 7,9% |
| 2025 | 8,0% |

Em 2021, quase toda resposta "Sim" era validada; a partir de 2022, só ~8-11% são. Isso é uma mudança de processo/definição, independente da já conhecida mudança de régua entre 2023 e 2024. **Consequência prática: qualquer comparação de pontuação (ou de "quantas famílias têm critério validado") entre 2021 e os demais anos está comparando coisas diferentes.** Sem essa correção, 2021 mostrava um padrão contraintuitivo (inscrições canceladas com pontuação quase tão alta quanto as atendidas) que na verdade é artefato dessa quebra de definição, não uma falha real do sistema de pontuação naquele ano.

### 3.3 Ignorando 2021: a pontuação válida acompanha o desfecho na direção esperada

`% de inscrições com pontuação válida > 0`, por ano e desfecho (métrica robusta à forte concentração de zeros — entre 93,8% e 96,6% das inscrições de 2022-2025 têm score = 0):

| Ano | Atendida | Fila | Cancelada |
| --- | ---: | ---: | ---: |
| 2022 | 4,1% | 2,6% | 2,3% |
| 2023 | 4,8% | 3,5% | 2,4% |
| 2024 | 6,4% | 4,8% | 4,7% |
| 2025 | 7,0% | 4,7% | 4,4% |

Em todos os 4 anos, **Atendida > Fila ≥ Cancelada** — suporta H12: ter um critério de pontuação validado está de fato associado a um desfecho melhor.

### 3.4 Mas o que discrimina é "ter pontuação", não "quanto"

Entre as inscrições que **têm** pontuação positiva, a pontuação média (como % do teto do ano) é parecida entre os três desfechos — ex. em 2023: 99,8% (Atendida) vs. 98,2% (Fila) vs. 98,8% (Cancelada), quase idênticos. Ou seja, o poder discriminativo da régua parece vir majoritariamente de um efeito binário (ter ou não ter algum critério validado), não da magnitude do score — achado relevante para uma futura revisão do desenho da régua (menos perguntas de peso fino, mais foco em identificar corretamente quem tem direito a algum critério prioritário).

### 3.5 Inscrições sem nenhuma resposta em B (2,4%, 8.162 casos)

| Desfecho | n |
| --- | ---: |
| Cancelada | 4.640 |
| Fila | 3.239 |
| Atendida | 283 |

A maioria termina cancelada — plausivelmente inscrições abandonadas pela própria família antes de responder o questionário socioeconômico, mas vale validar essa leitura com mais uma fonte (ex.: tempo entre `data_criacao` e o cancelamento) antes de tratar como conclusão.

---

## 4. Aprofundamento — quem nunca é convocado x quem perde na confirmação (foco 2024-2025)

A "perda total" (Cancelada, sem atendimento e sem fila) não é um grupo homogêneo. Analisando **só os anos recentes (2024-2025)** — o período sob a régua de pontuação atual e mais relevante para qualquer recomendação — dá pra separar por que cada inscrição some do processo, usando o tipo de cancelamento presente nas suas opções.

### 4.1 Funil geral, 2024-2025 combinado (154.639 inscrições)

| Desfecho | n | % |
| --- | ---: | ---: |
| Atendida | 100.924 | 65,3% |
| **Perda total** | **31.502** | **20,4%** |
| Fila | 22.213 | 14,4% |

A taxa de perda total em 2024-2025 (20,4%) é praticamente igual à média histórica dos 5 anos (20,6%) — não é um problema que esteja piorando isoladamente, mesmo com o `Cancelado pelo sistema` bruto subindo nesse período (ver seção 2.3).

### 4.2 Composição da perda total, 2024-2025 combinado

| Assinatura | n | % | Leitura |
| --- | ---: | ---: | --- |
| Só `Cancelado pelo sistema` | 13.439 | 42,7% | Nunca chegou a ser convocada |
| Só `Cancelado na confirmacao` | 10.296 | 32,7% | Foi convocada, perdeu na etapa de confirmação |
| Só `Cancelado` (simples) | 5.850 | 18,6% | Provável cancelamento manual/pela família |
| Misto (mais de um tipo entre as opções) | 1.917 | 6,1% | — |

Ou seja, em 2024-2025: **43% nunca são de fato chamadas**, mas **33% chegam a ser chamadas e perdem a vaga na confirmação** — quase 1 em cada 3 perdas totais é fricção de processo, não falta de prioridade. O `Cancelado` simples (18,6%) é bem mais relevante aqui do que era em 2021-2023 (~1-4%), uma mudança de composição que vale investigar com alguém da SME (possível mudança de rotulagem/processo na mesma reforma de 2024).

### 4.3 Opções registradas e pontuação, 2024-2025 combinado

- Média de **2,13 opções** por inscrição perdida, e **48,2% registrou uma única opção** — quase metade da perda total nunca teve uma segunda chance dentro da própria inscrição.
- % com pontuação válida positiva (score>0) é baixo e parecido entre os quatro tipos de cancelamento (2,7%-5,3%) — a pontuação não é o que diferencia quem nunca é chamado de quem perde na confirmação.
- Para contexto, olhando os três desfechos em 2024-2025: Atendida 6,7% > Fila 4,7% ≈ Cancelada 4,6% de score positivo — direção esperada, mas a diferença entre Fila e Cancelada é pequena nesse recorte mais recente.

## 5. Perguntas novas que emergiram (candidatas a próxima rodada)

1. Por que a taxa de "Cancelado pelo sistema" sobe de ~34-36% (2021-2023) para ~43-44% (2024-2025)? Coincide com a reforma da régua — é causa ou coincidência?
2. Por que a taxa de validação (`confirmado` dado `resposta='Sim'`) despenca de 2021 para 2022? Mudança de processo administrativo, ou artefato da extração?
3. As 8.162 inscrições sem nenhuma resposta em B: são abandono precoce da família ou falha de coleta? Testável cruzando com `data_criacao` (abandono logo após criar a inscrição vs. inscrição antiga sem resposta).
4. Dado que "ter pontuação" importa mais que "quanto", quais perguntas específicas (via `perg_id`) são as que mais aparecem entre quem tem score > 0 — vale revisitar H16 (concentração de peso em poucos critérios) com esse recorte.
5. O que explica o salto do `Cancelado` simples dentro da perda total, de ~1-4% (2021-2023) para 18,6% em 2024-2025? Parece uma mudança de processo/rotulagem administrativa coincidindo com a reforma da régua — vale confirmar com a SME.
6. Para o ~33% da perda total 2024-2025 que é "convocada mas perde na confirmação": quanto tempo essas famílias tinham entre a convocação e o prazo de confirmação? Se for um prazo curto ou pouco divulgado, é uma alavanca de eficiência de baixo custo (lembrete, extensão de prazo) — mas a base atual não tem timestamp de convocação/confirmação, só `data_criacao` da opção.
