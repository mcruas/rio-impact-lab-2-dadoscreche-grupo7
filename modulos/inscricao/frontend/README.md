# Inscrição — Frontend (Tela 1 + fluxo de match)

Protótipo em React + TypeScript (Vite), mobile-first: **passos 1-5 são a Tela 1
(inscrição)** e **passos 6-9 são o fluxo de match (pós-inscrição)**.
Padrão visual (cores, componentes, cópia dos textos, os 5 passos) definido a partir de
`imagem_telas_2.jpg` (raiz do repo) — essa versão substituiu por completo a v1
(`imagem_telas_1.jpg`), que tinha um fluxo diferente (turno como passo separado,
"locais de interesse" com até 3 endereços, favoritar em vez de ordenar). As telas
6-9 vêm de `tela_match_1.jpeg` (raiz do repo).

**Estado atual: busca por bairro/CEP (passo 2) e ranking (passo 3) já são reais**,
chamando o backend `recomendacao-escolas` de verdade (`GET /cep/{cep}` +
`POST /recomendacoes`). "Buscar por creche" (nome) continua mockado — o backend não
tem busca por nome ainda. Ver [`../README.md`](../README.md) para os contratos.

## Configuração

Copie `.env.example` para `.env.local` e ajuste `VITE_API_RECOMENDACAO_URL` se o
backend não estiver em `http://localhost:8000` (padrão). Precisa do backend
`recomendacao-escolas` rodando (ver `../recomendacao-escolas/README.md`) para o
passo 2 no modo "bairro/CEP" funcionar.

## Passos

1. **Dados da criança e do responsável** — nome, CPF da criança (com validador de
   dígitos verificadores — ver `src/utils/cpf.ts`), data de nascimento, turno
   Integral/Parcial, CPF do responsável (mesma validação). **Não pede CEP**: o
   endereço de referência é escolhido no passo 2, que é onde ele de fato importa
   (e onde a família pode procurar perto do trabalho ou da avó em vez de casa).
2. **Encontre sua creche** — alterna entre busca por nome (mockada,
   `src/data/mockCreches.ts`) e busca por bairro/CEP (real — `src/api/recomendacaoEscolas.ts`
   resolve CEP via `GET /cep/{cep}` quando o texto parece CEP, depois chama
   `POST /recomendacoes`). Traz **20 candidatas** (`TOTAL_CANDIDATAS`), não 5: as 5
   melhores viram a lista inicial e as outras 15 ficam no mapa do passo 3 para a
   família trocar. Mostra erro se o backend estiver fora do ar ou o CEP não existir.
3. **Escolha e ordene até 5 creches** — lista arrastável (`@dnd-kit`, com suporte a
   toque) sobre os resultados reais da busca (`dados.resultadosBusca`). O mapa mostra
   as 20 candidatas: **tocar num pino cinza adiciona a creche à lista**; no limite de
   5 (`LIMITE_ESCOLHAS`) o clique não adiciona e aparece um aviso pedindo para
   remover alguma antes — remover é só pelo "×" do card, porque remover sem querer
   com o dedo no mapa seria fácil demais. Um modal de "sugestão de troca" aparece
   automaticamente quando alguma candidata fora do top 5 tem `pontuacaoFinal` maior
   que a 3ª escolha atual — usa o racional de verdade (`rationale.explicacao`)
   devolvido pelo backend, não um texto inventado.
4. **Prioridade da inscrição** — CadÚnico, Bolsa Família, público-alvo de Educação
   Especial, outra vulnerabilidade — essas respostas são o que futuramente vira
   `POST /score-preliminar` no `match-engine` (endpoint ainda não implementado lá).
5. **Confirmação** — tela de sucesso, com "próximos passos" citando os módulos
   `documentacao/` e `acompanhamento/`. "Acompanhar inscrição" entra no fluxo de
   match (passo 6).

## Fluxo de match (passos 6-9, pós-inscrição)

No sistema real esse fluxo seria disparado pelo Motor de Match dias depois, e as
telas leriam o estado da inscrição em `match-engine`/`acompanhamento`. **Aqui não há
backend nenhum**: as telas são alimentadas pelos dados que a família já preencheu nos
passos 1-4 — nada é inventado, e o que não dá pra derivar aparece como estado vazio.

6. **Match encontrado** — a vaga mostrada é a **1ª escolha** do passo 3
   (`utils/creches.ts::crecheDoMatch`). O "por que essa vaga combina com você" é
   montado dos dados reais: posição na lista, faixa etária calculada da data de
   nascimento, turno escolhido e a `distanciaKm` devolvida pelo backend de
   recomendação. Sem creche escolhida, mostra estado vazio em vez de uma vaga fake.
7. **Confirmar vaga / documentos** — escolha entre enviar pelo app ou levar à
   escola (guardada em `dados.envioDocumentos`); "Continuar" só habilita depois de
   escolher. A lista de documentos é uma **lista de referência do protótipo** (a
   oficial é do módulo `documentacao/`), com itens condicionais às respostas do
   passo 4 — só pede comprovação do que a família declarou (CadÚnico, Bolsa
   Família, laudo de Educação Especial, outra vulnerabilidade).
8. **Em análise** — prazo e canais de aviso; "Ver detalhes da inscrição" abre o
   resumo do que foi preenchido. O botão "Ver resultado da análise" existe só para
   o protótipo poder avançar (está rotulado como tal na tela).
9. **Matrícula confirmada** — endereço da unidade (vem do dataset de escolas; é
   nulo no fallback de busca por nome), prazo para comparecer e comprovante
   (`window.alert`, sem PDF).

A faixa etária ("Maternal I" etc.) é calculada da data de nascimento contra a data
de corte de 31/03 do ano corrente — é só exibição, quem define a turma é a unidade.

Um **painel de teste** (`components/PainelTeste.tsx`, visível abaixo do cabeçalho,
com borda tracejada laranja para não ser confundido com o design real) preenche os
campos simples (passos 1 e 4) com `DADOS_EXEMPLO` e deixa pular direto para qualquer
passo, em duas linhas ("Inscrição" 1-5 e "Match" 6-9) — não simula um resultado de
busca (os passos 3 e 6-9 só têm conteúdo depois que o passo 2 buscar de verdade).

## Estrutura

```
src/
├── app.css, index.css        — estilo (tokens de cor/espaçamento em index.css)
├── types.ts                  — tipos TS espelhando os contracts/schemas usados aqui
├── utils/cpf.ts               — máscara + validação de CPF (formato e dígitos verificadores)
├── utils/creches.ts           — buscarCreche/crecheDoMatch, faixa etária, distância
├── api/recomendacaoEscolas.ts — cliente HTTP do backend (GET /cep, POST /recomendacoes)
├── data/mockCreches.ts       — fallback do modo "buscar por creche" + DADOS_EXEMPLO
├── components/                — StepShell, ProgressDots, PillGroup, SegmentedToggle,
│                                 CampoCpf, OrderableSchoolCard, CrecheTags,
│                                 SwapSuggestionModal, BrandHeader, PainelTeste,
│                                 MapaCreches, e do fluxo de match: MatchHeader,
│                                 MatchStepper, CardVaga, AvisoSemVaga
└── steps/                     — um componente por passo (Step1Dados...Step9Matricula)
```

`App.tsx` guarda o estado do formulário inteiro e o passo atual (sem lib de
roteamento/estado — não precisa nesta escala).

## Rodar localmente

```bash
npm install
npm run dev      # abre em http://localhost:5173
npm run build    # build de produção (tsc -b && vite build)
npm run lint      # oxlint
```

## Próximos passos (fora do escopo desta rodada)

- Busca por nome de creche de verdade (precisa de um endpoint novo em
  `recomendacao-escolas`, hoje só busca por bairro).
- `score_estimado`/`historico_responsavel` de verdade (precisa dos endpoints
  `POST /score-preliminar`/`GET /historico/{cpf}` no `match-engine`, hoje só
  propostos no contrato, não implementados).
- Persistir a inscrição de verdade via `POST /inscricoes` (backend próprio deste
  módulo, hoje só um stub em `../backend/main.py`).
- Filtrar as candidatas por oferta de creche: `POST /recomendacoes` rankeia todas as
  unidades do dataset, então entre as 20 mais próximas aparecem Escolas Municipais,
  CIEPs e escolas especiais que podem não ter turma de creche. Com 8 resultados isso
  passava batido; com 20 no mapa fica visível. Precisa de um critério acordado (por
  `tipo`? por oferta declarada?) antes de sair filtrando.
- Ligar as telas 6-9 no `match-engine`/`acompanhamento` de verdade: hoje a "vaga do
  match" é a 1ª escolha da família, não o resultado do motor, e o avanço entre
  análise e matrícula é um clique em vez de um evento do backend.
- Upload real dos documentos (módulo `documentacao/`) e comprovante em PDF — hoje
  os dois são `window.alert`/estado local.
- A barra de abas inferior (Início/Inscrição/Mensagens/Perfil) do desenho ficou de
  fora: o protótipo tem só este fluxo, então ela não navegaria para lugar nenhum.
