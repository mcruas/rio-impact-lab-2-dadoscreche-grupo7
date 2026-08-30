# Problemas identificados

Registro de trabalho do hackathon. Um problema por seção: o que é, o que os dados
mostram, a solução proposta e as ressalvas conhecidas. Números referem-se ao
processo de 2025 salvo indicação contrária.

> Os dados da SME são anonimizados por randomização, generalização e supressão.
> Valores absolutos não representam a realidade; a estrutura dos problemas, sim.

> Ver também [`eda/RESULTADOS_MATCHING.md`](eda/RESULTADOS_MATCHING.md) para como estes achados se cruzam com a EDA do grupo (H1-H16, `eda/HIPOTESES_EDA.md` e `eda/RESULTADOS_H6_H12.md`).

---

## P1 — Quase metade das famílias lista uma única opção

**Status:** aberto · **Eixos:** 2 (classificação), 1 (planejamento)

### O problema

Das 71.949 inscrições de 2025, **33.835 (47,0%) indicaram apenas uma creche**,
tendo direito a cinco. A família concentra toda a sua chance numa única unidade —
em geral a mais próxima ou a mais conhecida — e, se a fila daquela unidade não
andar, ela termina o processo sem nada, mesmo havendo vaga ociosa ao lado.

| Opções listadas | Inscrições | % do total |
| ---: | ---: | ---: |
| 1 | 33.835 | 47,0% |
| 2 | 12.764 | 17,7% |
| 3 | 10.350 | 14,4% |
| 4 | 5.434 | 7,6% |
| 5 | 9.566 | 13,3% |

### Solução proposta

Sugerir unidades no ato da inscrição a partir do **endereço de residência**,
ordenadas por proximidade e por disponibilidade projetada de vaga. O sistema já
tem os dois insumos: CEP e bairro do responsável, e a ocupação por unidade,
grupamento e turno.

### O que os dados dizem

**O tamanho do prêmio é grande.** Das inscrições de opção única que terminaram sem
vaga (10.637), **58,9% tinham vaga ociosa no próprio bairro**, no mesmo grupamento
e turno que pediram. Limitando pela capacidade que de fato existe, **2.348 crianças
seriam absorvidas** — cerca de 30% de toda a fila de 2025.

**Mas a sugestão sozinha não entrega isso.** Comparando famílias do mesmo bairro,
grupamento e turno, listar três ou mais opções em vez de uma aumenta a chance de
vaga em apenas **2,6 pontos percentuais** (66,1% → 68,7%), e só ajuda em 120 dos
198 estratos comparáveis — pouco acima de um cara ou coroa.

### Ressalva importante

Listar mais opções rende pouco hoje porque a classificação **não é um matching**:
são filas independentes por unidade, turno e grupamento, com a mesma criança em
várias delas. Num mecanismo de aceitação diferida, listar mais opções nunca pode
prejudicar e quase sempre melhora — é o que torna a sugestão eficaz.

**Conclusão: P1 é necessário, mas não suficiente.** Entregar a sugestão sem trocar
o mecanismo de classificação convida a família a listar opções que o sistema não
usa de verdade. A dupla sugestão + aceitação diferida é o que converte os 2.348.

### Como medir se funcionou

- % de inscrições com mais de uma opção (linha de base: 53,0%)
- % da fila residual com vaga ociosa disponível no próprio bairro (base: 58,9%)
- crianças sem vaga ao fim do processo (base: 8.351)

---

## P2 — O sistema oferta até 5 vagas para a mesma criança

**Status:** aberto · **Eixos:** 2 (classificação), 3 (convocação)
**Fonte:** apresentação da SME, slide "Eixo 2 — onde a lógica quebra", confirmado nos dados

### O problema

A própria SME descreve o mecanismo: *"o processo de classificação é orientado pelo
total de escolhas por unidade, e não por CPF"* e *"o sistema classifica as opções
simultaneamente: ofertando até 5 vagas para o mesmo CPF"*.

Cada unidade mantém sua própria fila e classifica sem saber o que as outras estão
fazendo. Uma criança bem pontuada é chamada em várias unidades ao mesmo tempo e
congela todas as vagas até decidir — enquanto outra criança espera.

### O que os dados dizem

Contando ofertas por criança (`Confirmado`, `Selecionado`, `Selecionado da lista`
e `Cancelado na confirmacao`) em 2025:

| Ano | Crianças com oferta | Ofertas emitidas | **Ofertas excedentes** | % desperdício |
| ---: | ---: | ---: | ---: | ---: |
| 2021 | 39.398 | 57.009 | 17.611 | 30,9% |
| 2023 | 36.759 | 50.311 | 13.552 | 26,9% |
| 2025 | 54.760 | 66.629 | **11.869** | **17,8%** |

**7.231 crianças receberam oferta em duas ou mais unidades em 2025** — uma delas em
seis. As 11.869 ofertas excedentes **superam em 49% a fila de espera inteira**
(7.969 crianças).

### Solução proposta

Aceitação diferida em lote, com a chave da alocação sendo a **criança**, não a
opção. Cada criança recebe no máximo uma oferta por rodada. O que hoje é oferta
excedente vira vaga oferecida a quem está sem nada.

### Ressalva

O número de ofertas excedentes não é o número de crianças que seriam atendidas: a
vaga congelada e a criança na fila precisam ser do mesmo grupamento, turno e
território. O teto realista é o casamento territorial calculado no diagnóstico —
não a soma bruta.

---

## P3 — CadÚnico decide metade da fila e é conferido à mão

**Status:** aberto · **Eixos:** 2 (classificação)
**Fonte:** apresentação da SME, slide "A jornada da Inscrição Creche"

### O problema

A régua de 2025 dá **51 pontos ao CadÚnico** — sozinho, o maior peso. Na prática a
classificação responde a uma pergunta só: 48,9% das crianças somam 51 ou mais
pontos, 49,0% somam até 6.

Mas a SME registra que comprovar os critérios ainda depende de comparecimento
presencial na unidade dentro do prazo, documento físico, validação manual pela
escola e *"cruzamentos com bases oficiais mas sem integração entre sistemas"*
justamente para CadÚnico e Bolsa Família.

Ou seja: **o critério que decide metade da fila é verificado manualmente**, e a
família que não consegue ir à unidade no prazo perde a pontuação que teria direito.

### Solução proposta

Integrar a verificação ao **Registro Municipal Integrado** — que já existe, já é
usado na etapa 4 do fluxo de classificação e tem API documentada em
`docs.dados.rio/rmi/overview`. A pontuação passa a ser conferida na inscrição, não
no balcão.

### Efeito colateral que interessa

Isso reduz uma barreira que hoje filtra exatamente quem o critério quer proteger:
a família que não pode faltar ao trabalho para levar papel na creche.

### O que ainda não sei

Se o RMI cobre CadÚnico com cobertura e latência suficientes, e qual o vínculo
disponível (CPF do responsável). Precisa ser confirmado com a equipe da SME.

---

## P4 — Estados transitórios não sinalizados

**Status:** aberto · **Eixos:** 3 (convocação)
**Fonte:** apresentação da SME, gap "Estados transitórios não sinalizados"; confirmado nos dados

### O problema

Em algum momento do fluxo, uma opção do cadastro fica "Selecionado" (vaga
ofertada, aguardando confirmação) enquanto outra opção do **mesmo** cadastro
segue em "Lista de espera". Sem painel, ninguém vê isso até virar reclamação.

### O que os dados dizem

A SME estima ~0,2%. Medido ano a ano:

| Ano | Cadastros inconsistentes | Total | % |
| ---: | ---: | ---: | ---: |
| 2021 | 48 | 73.283 | 0,07% |
| 2022 | 219 | 64.055 | 0,34% |
| 2023 | 121 | 51.331 | 0,24% |
| 2024 | 229 | 82.690 | 0,28% |
| 2025 | 51 | 71.949 | 0,07% |

Bate com a estimativa da SME. Baixo volume, mas cada caso é uma família que
pode perder a vaga por não saber que precisa agir — e não escala com equipe
humana revendo linha a linha.

### Solução

Consequência direta do log de eventos do Eixo 3 (ver `ARQUITETURA.md`): uma
regra simples sobre o log ("mesmo cadastro com uma opção Selecionado e outra
em Lista de espera") vira alerta automático, não auditoria manual.

---

## P5 — Colisão de identidade quando falta CPF/DNV/NIS

**Status:** aberto · **Eixos:** transversal — compromete a integridade de
qualquer contagem por criança, inclusive as deste diagnóstico
**Fonte:** apresentação da SME, gap "Identificação da criança sujeita a
colisão"; quantificado nos dados, achado maior do que o esperado

### O problema

Sem CPF, DNV ou NIS, a anonimização agrupa pela chave nome normalizado +
data de nascimento. Duas crianças diferentes com nome e nascimento
parecidos — comum em famílias grandes ou nomes populares — podem cair no
mesmo código `aluno_anon`.

### O que os dados dizem

Testei o que é fisicamente impossível para uma criança real: o mesmo código,
com sexo ou mês de nascimento diferentes entre as próprias opções.

| Verificação | Códigos afetados | Base | % |
| --- | ---: | ---: | ---: |
| Sexo inconsistente, mesmo ano | 1.502 | 296.084 código-ano | 0,51% |
| Nascimento inconsistente, mesmo ano | 455 | 296.084 código-ano | 0,15% |
| Sexo inconsistente, entre anos | 2.101 | 34.486 crianças multi-ano | **6,1%** |
| Nascimento inconsistente, entre anos | 406 | 34.486 crianças multi-ano | 1,2% |
| Mesmo código, 2+ cadastros reais distintos, mesmo ano (2025) | 431 | 71.930 cadastros | 0,60% |

**O ponto crítico:** o README da SME cita as 34.486 crianças que reaparecem em
mais de um ano como prova de que a trajetória é preservada pela anonimização.
Medido agora, **6,1% dessas "reaparições" são fisicamente impossíveis** — são
colisões, não a mesma criança voltando.

**A colisão também acontece dentro do mesmo ano**, sem precisar do teste de
sexo/nascimento: dentro de um cadastro real `(prm_id,plm_id,ipl_id)` a
pontuação de classificação é sempre a mesma (0 de 71.930 cadastros de 2025
contradizem isso), mas 431 códigos `aluno_anon` de 2025 aparecem ligados a
mais de um cadastro real diferente — dois cadastros reais, pontuações
possivelmente diferentes, mesmo código. Achado ao tentar entender por que o
motor de matching via pontuação "inconsistente" para uma mesma criança; a
causa não era a régua, era o código compartilhado.

### Por que isso importa para o resto do projeto

Qualquer métrica que trate `aluno_anon` como identidade estável de uma
criança real carrega esse ruído — incluindo a taxa de retorno à fila que citei
no diagnóstico inicial (57,1% em 2024) e o próprio backtest do motor de
matching (`MATCHING.md`), que usa o código como chave de alocação. O ruído é
pequeno (~0,5% dentro do mesmo ano) mas não é zero, e cresce quando se olha
através de anos.

### Solução

Fora do nosso alcance no hackathon — é dado de origem, não algo que se
corrige na anonimização já feita. Mas é o argumento mais forte para a
prefeitura acelerar cobertura de CPF/DNV/NIS na inscrição: cada campo
preenchido elimina colisão por construção, sem precisar de nenhum algoritmo.

### Ressalva

Isso é uma cota mínima de colisão — o teste só pega os casos em que sexo ou
mês de nascimento mudam. Uma colisão entre duas meninas nascidas no mesmo mês
não deixa rastro nesse teste e não é capturada. O número real é maior que
0,51%.

---

## P6 — Fila sem registro de tempo

**Status:** aberto · **Eixos:** 3 (convocação) — pré-requisito para medir
qualquer coisa no Eixo 3
**Fonte:** apresentação da SME, gap "Fila sem visibilidade de prazo"

### O problema

A base só tem `data_criacao` (quando a inscrição foi criada). Não existe
registro de quando uma opção mudou de status — quando virou "Selecionado",
há quanto tempo está "aguardando confirmação", quando virou "Cancelado pelo
sistema". Sem isso, ninguém mede SLA, e a equipe da CRE não sabe quais vagas
estão "penduradas" até vencer o prazo.

### Por que isso não é um problema entre outros

É o pré-requisito de tudo no Eixo 3. Não dá para calibrar overbooking, medir
taxa de não-confirmação por unidade em tempo real, ou automatizar o P4 sem um
log de eventos com timestamp. Já está registrado como a primeira peça do
Eixo 3 em `ARQUITETURA.md`; esta entrada existe para deixar explícito que é
também um dos cinco gaps que a própria SME nomeou, não uma invenção nossa.

### Solução

Tabela de eventos: `(prm_id, plm_id, ipl_id, opcao, status_anterior,
status_novo, timestamp, canal, resultado)`. Populada pela mesma pipeline que
hoje só grava o estado final.
