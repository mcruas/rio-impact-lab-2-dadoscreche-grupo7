# Inscrição — Frontend (Tela 1)

Protótipo dos 5 passos da Tela 1, em React + TypeScript (Vite), mobile-first.
Padrão visual (cores, componentes, cópia dos textos, os 5 passos) definido a partir de
`imagem_telas_2.jpg` (raiz do repo) — essa versão substituiu por completo a v1
(`imagem_telas_1.jpg`), que tinha um fluxo diferente (turno como passo separado,
"locais de interesse" com até 3 endereços, favoritar em vez de ordenar).

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
   Integral/Parcial, CPF do responsável (mesma validação), CEP residencial.
2. **Encontre sua creche** — alterna entre busca por nome (mockada,
   `src/data/mockCreches.ts`) e busca por bairro/CEP (real — `src/api/recomendacaoEscolas.ts`
   resolve CEP via `GET /cep/{cep}` quando o texto parece CEP, depois chama
   `POST /recomendacoes`). Mostra erro se o backend estiver fora do ar ou o CEP não
   existir.
3. **Escolha e ordene até 5 creches** — lista arrastável (`@dnd-kit`, com suporte a
   toque) sobre os resultados reais da busca (`dados.resultadosBusca`). Um modal de
   "sugestão de troca" aparece automaticamente quando alguma candidata fora do top 5
   tem `pontuacaoFinal` maior que a 3ª escolha atual — usa o racional de verdade
   (`rationale.explicacao`) devolvido pelo backend, não um texto inventado.
4. **Prioridade da inscrição** — CadÚnico, Bolsa Família, público-alvo de Educação
   Especial, outra vulnerabilidade — essas respostas são o que futuramente vira
   `POST /score-preliminar` no `match-engine` (endpoint ainda não implementado lá).
5. **Confirmação** — tela de sucesso, com "próximos passos" citando os módulos
   `documentacao/` e `acompanhamento/`.

Um **painel de teste** (`components/PainelTeste.tsx`, visível abaixo do cabeçalho,
com borda tracejada laranja para não ser confundido com o design real) preenche os
campos simples (passos 1 e 4) com `DADOS_EXEMPLO` e deixa pular direto para qualquer
passo — não simula um resultado de busca (o passo 3 só tem conteúdo depois que o
passo 2 buscar de verdade).

## Estrutura

```
src/
├── app.css, index.css        — estilo (tokens de cor/espaçamento em index.css)
├── types.ts                  — tipos TS espelhando os contracts/schemas usados aqui
├── utils/cpf.ts               — máscara + validação de CPF (formato e dígitos verificadores)
├── api/recomendacaoEscolas.ts — cliente HTTP do backend (GET /cep, POST /recomendacoes)
├── data/mockCreches.ts       — fallback do modo "buscar por creche" + DADOS_EXEMPLO
├── components/                — StepShell, ProgressDots, PillGroup, SegmentedToggle,
│                                 CampoCpf, OrderableSchoolCard, CrecheTags,
│                                 SwapSuggestionModal, BrandHeader, PainelTeste
└── steps/                     — um componente por passo (Step1Dados...Step5Confirmacao)
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
- Validação de CEP no campo de endereço residencial do passo 1 (hoje só o passo 2
  resolve CEP de verdade; o CEP do passo 1 ainda só checa se não está vazio).
