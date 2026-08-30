# Reconciliação com H1-H16 e proposta de mecanismo de matching

> Este documento faz a ponte entre a EDA do grupo ([`HIPOTESES_EDA.md`](HIPOTESES_EDA.md),
> [`RESULTADOS_H6_H12.md`](RESULTADOS_H6_H12.md)) e um segundo levantamento, feito em
> paralelo, que chegou a um diagnóstico (`PROBLEMAS.md`, raiz do repo) e a uma proposta de
> mecanismo de alocação (`MATCHING.md` + `motor/`, raiz do repo). Os dois trabalhos usaram
> as mesmas bases (Query A/B/C) mas fizeram perguntas diferentes — este documento cruza os
> dois para não deixar achado paralelo sem checagem, e para que quem ler não precise
> reconstruir sozinho onde um confirma o outro.

## Como ler isto

- **P1-P6** = problemas registrados em `PROBLEMAS.md` (diagnóstico + solução proposta).
- **H1-H16** = hipóteses de `HIPOTESES_EDA.md`; H6 e H12 já têm resultado em `RESULTADOS_H6_H12.md`.
- Onde os dois convergem, isso é evidência mais forte (duas metodologias independentes, mesma
  conclusão). Onde divergem na superfície, investiguei até entender se é conflito real ou
  diferença de metodologia — nenhum caso abaixo ficou como conflito real.

## P3 ↔ H12 — convergem, e a diferença de métrica explica tudo

**H12** mediu se a pontuação **validada** (`resposta='Sim' AND confirmado='Sim'`) prediz o
desfecho, e concluiu que sim — mas o que discrimina é **ter algum critério validado, não o
valor exato da pontuação** (2023: 99,8% do teto entre os Atendidos vs. 98,2% entre os que
ficaram na fila — quase idênticos entre quem tem pontuação positiva).

**P3** mediu se a pontuação **declarada** prediz o desfecho, e a resposta é: praticamente
zero. P(vaga) por pontos declarados, 2025: 0 pts → 67,7%; 51 pts (CadÚnico) → 65,5%; 53 pts →
68,7%; 78 pts → 68,5%. Curva chapada. Restringindo a estratos disputados
(demanda > 1,5× vagas), a relação chega a inverter (≥51 → 28,7%, <51 → 31,4%).

**Não há conflito — são a mesma verdade vista de dois ângulos.** H12 mede pontuação
*validada*; P3 mede pontuação *declarada*. A ponte entre as duas é exatamente o achado que os
dois levantamentos fizeram, de formas independentes:

| | H12 (`RESULTADOS_H6_H12.md`) | P3 (`PROBLEMAS.md`) |
|---|---|---|
| Taxa de validação (`confirmado='Sim'` dado `resposta='Sim'`), 2025 | **8,0%** (todas as perguntas) | **6,8%** (CadÚnico especificamente) |
| Conclusão | Pontuação validada discrimina desfecho (binário: tem ou não tem) | Pontuação confirmada funciona (+18,5pp em estratos disputados); pontuação declarada, não |

Os dois números de validação (8,0% geral, 6,8% para CadÚnico) são consistentes entre si — o
CadÚnico fica levemente abaixo da média geral, mas na mesma ordem de grandeza. **A régua
funciona quando é verificada; quase nunca é verificada; e o que sobra (pontuação declarada,
usada por quase todo o processo) não discrimina nada.** Essa é a frase que teria ficado
incompleta em qualquer um dos dois documentos sozinho.

Verifiquei antes de escrever isto: recomputei `pontos_confirmados` do zero, direto de Query B
+ Query C, usando a regra `resposta='Sim' AND confirmado='Sim'` que H12 identificou como
correta (a alternativa, `confirmado='Sim'` sozinho, infla o score). Os dois métodos batem em
**71.930 de 71.930 cadastros de 2025** — o número usado no P3 já estava certo, não por
sorte, mas porque calculei os pontos como soma agregada por cadastro a partir da mesma regra,
sem perceber que era a mesma regra que H12 nomeou explicitamente. Registro isso porque é
exatamente o tipo de erro silencioso que H12 avisa que existe.

## P1 ↔ H11 — mesma conclusão de política, precisão diferente

**H11** (refutada): escolher mais opções não muda a taxa de atendimento — fica entre 54% e
58% de 1 a 5 opções, olhando o agregado bruto.

**P1**: comparando famílias do **mesmo bairro, grupamento e turno** (controlando o confundidor
óbvio — quem lista mais opções pode morar em região com mais oferta), listar 3+ opções sobe a
chance de vaga de 66,1% para 68,7%: **+2,6pp**, e só ajuda em 120 dos 198 estratos
comparáveis.

**Mesma conclusão de política nos dois:** orientar famílias a listar mais opções, isoladamente,
não é uma alavanca de eficiência que resolve o problema. A diferença entre "completamente
plano" (H11) e "+2,6pp, quase cara ou coroa" (P1) é o efeito de controlar por território/
grupamento/turno — o pequeno resíduo positivo em P1 é provavelmente o que sobra depois de
remover o confundidor territorial que H11 não isolou. Nenhum dos dois sustenta "liste mais
opções" como solução sozinha — os dois apontam para o mesmo lugar: **o gargalo é o mecanismo de
classificação (filas independentes por unidade, sem território), não a quantidade de opções**,
que é a tese central de `MATCHING.md`.

## P5 ↔ achado de qualidade #4 (`RESULTADOS_H6_H12.md`) — mesmo problema, métodos complementares

O grupo já tinha achado e corrigido: **~696 códigos `aluno_anon` são "baldes" de crianças não
identificáveis** (detectado via `COUNT(DISTINCT nascimento_aluno_anomes) > 1` por código; 3.465
linhas, 0,4% de Query A — ex. `aluno_0000003`, 192 aparições, 43 datas de nascimento e 141
responsáveis diferentes).

P5 usou outro filtro, mais fino: sexo ou mês de nascimento **fisicamente impossíveis** de
mudar para a mesma criança, dentro do mesmo ano (1.502/455 casos, 2025) e entre anos, entre as
34.486 crianças que a documentação da SME cita como "reaparecem" (2.101/406, **6,1%**
fisicamente impossíveis). Achei também 431 códigos de 2025 com dois cadastros reais
diferentes por trás do mesmo código — descoberto ao investigar uma pontuação
aparentemente "inconsistente" entre opções da mesma criança no motor de matching.

**Os dois métodos não competem, se complementam por sensibilidade:** o filtro do grupo
(`COUNT(DISTINCT nascimento) > 1`) pega os casos extremos — "baldes" degenerados como
`aluno_0000003`, com dezenas ou centenas de aparições, quase certamente o código de fallback da
anonimização para registros sem CPF/DNV/NIS suficiente. O filtro de P5 (sexo/nascimento
impossível) pega colisões **sutis** — duas crianças reais diferentes, cada uma com poucas
inscrições, que por acaso caem no mesmo código — que o filtro do grupo não isola porque nunca
teria um `COUNT(DISTINCT nascimento)` chamativo. **Recomendação para qualquer análise por
criança:** aplicar os dois filtros, não um no lugar do outro. Nenhum dos dois é o teto real —
uma colisão entre duas crianças do mesmo sexo, nascidas no mesmo mês, não deixa rastro em
nenhum dos dois testes.

## O que este levantamento acrescenta, sem sobreposição com H1-H16

Três problemas vieram de uma fonte que a EDA de Query A/B/C não cobre — a apresentação da
própria SME sobre o desafio (`desafio/Apresentação-problema.pdf`):

- **P2** — o sistema oferta até 5 vagas simultâneas para o mesmo CPF (palavras da própria SME);
  11.869 ofertas excedentes em 2025, mais que a fila de espera inteira.
- **P4** — estados transitórios não sinalizados (mesmo cadastro com uma opção `Selecionado` e
  outra em `Lista de espera`); confirmado nos dados, ~0,07-0,34% ao ano, batendo com a
  estimativa da própria SME.
- **P6** — fila sem registro de tempo (só existe `data_criacao`, não um log de mudança de
  status) — pré-requisito para automatizar qualquer coisa no Eixo 3 (convocação), incluindo
  medir o prazo de confirmação que a pergunta 6 de `RESULTADOS_H6_H12.md` deixa em aberto.

E uma peça que nenhuma EDA sozinha entrega — **o que fazer com o diagnóstico**: `MATCHING.md`
e `motor/matching.py` propõem e testam (aceitação diferida com reserva territorial mole,
desempate por sorteio único, os dois critérios de desempate legais da Query C) um mecanismo
que resolve P1+P2 ao mesmo tempo — sugestão de unidade só funciona se listar mais opções for
seguro, e isso exige trocar o mecanismo de classificação, não só a interface de inscrição.
Backtest sobre os 62.891 cadastros de 2025 no próprio `MATCHING.md`.

## Pergunta em aberto que H12 levanta e P3 não resolve

`RESULTADOS_H6_H12.md` pergunta (seção 5, item 2): por que a taxa de validação despenca de
88,9% (2021) para ~8-11% (2022+)? P3 não investiga a causa dessa queda — só usa o número de
2025 (8,0%/6,8%) como estava. Vale investigar se é mudança de processo (a própria SME
documenta, na apresentação, que a verificação de CadÚnico/Bolsa Família depende de
comparecimento presencial — mas isso não explica por que 2021 era diferente) ou artefato de
extração, antes de assumir que a solução proposta em P3 (integração via RMI) teria o mesmo
efeito em todos os anos.
