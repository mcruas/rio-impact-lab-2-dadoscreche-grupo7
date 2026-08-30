# Inscrição (Tela 1)

> Backend implementado: `POST /inscricoes` e `GET /inscricoes/{cpf}` persistem
> de verdade em Postgres (hospedado no Railway). Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura (esta pasta segue a mesma organização: `app/`, `api/index.py`,
> `vercel.json`).

## Responsabilidade

Dono da entidade `Inscricao` (contrato: [`../../contracts/inscricao.openapi.yaml`](../../contracts/inscricao.openapi.yaml)).
Tela de formulário onde o responsável cadastra:

- Nome da criança, CPF da criança, CPF do responsável, data de nascimento da criança
- Turno: Integral ou Parcial
- Endereço de casa (obrigatório) e até mais 2 lugares de interesse (rede de apoio, trabalho
  etc.) — `tipo` livre em cada item de `enderecos_interesse` (ver
  `contracts/schemas/endereco.schema.json`)
- Até 5 escolas escolhidas (a partir da recomendação trazida pelo módulo Recomendação de Escola)

## O que este módulo consome

- [`match-engine.openapi.yaml`](../../contracts/match-engine.openapi.yaml):
  - `POST /score-preliminar` — antes de chamar a recomendação, busca um score
    preliminar a partir de respostas socioeconômicas autodeclaradas (o score final,
    validado, só existe depois da Tela 2 + Motor de Match).
  - `GET /historico/{cpf}` — histórico de convocação/não-comparecimento do
    responsável (começa zerado para quem nunca se inscreveu antes).
- [`recomendacao-escolas.openapi.yaml`](../../contracts/recomendacao-escolas.openapi.yaml):
  - `POST /recomendacoes` — chamado com os endereços informados + o `score_estimado`
    e `historico_responsavel` obtidos acima (ambos opcionais/nulos se ainda não
    existirem — a recomendação funciona, só fica menos afinada). Devolve as escolas
    recomendadas com o racional de cada uma, para exibir junto na tela (a família tem
    o direito de entender por que uma escola foi ou não sugerida).

**Só por contrato** — nunca acessar o banco/código interno de `recomendacao-escolas/`
ou `match-engine/` diretamente.

## O que este módulo expõe

- `POST /inscricoes` — cria a inscrição (criança + responsável + endereços + escolas escolhidas)
  e persiste em Postgres. Validação de schema (CPF, endereço com `tipo=Moradia` obrigatório
  etc.) via os modelos Pydantic em `backend/app/models.py`, espelhando
  `contracts/schemas/inscricao.schema.json`.
- `GET /inscricoes/{cpf}` — busca pelo CPF da criança OU do responsável (o que existir
  primeiro), consultado pelo módulo `documentacao/` para confirmar que a inscrição existe
  antes de aceitar documentos. 404 se nenhuma inscrição bater com o CPF.

Persistência: `backend/app/db.py`, uma tabela única (`inscricoes`, com o documento completo
em `payload JSONB` e `cpf_crianca`/`cpf_responsavel` como colunas indexadas pra busca rápida).
Postgres provisionado no Railway; connection string em `DATABASE_URL` (ver
`backend/.env.example`) — sem esse env var configurado, o backend recusa (falha explícita,
não um fallback silencioso).

## Como começar

Backend (`backend/app/main.py` — mesma estrutura do `recomendacao-escolas/`):

```bash
cd modulos/inscricao/backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env.local   # preencher DATABASE_URL com a connection string do Postgres
uvicorn app.main:app --reload
```

Testes (não precisam de Postgres real — o repositório é substituído por um fake via
`app.dependency_overrides`):

```bash
pytest
```

Frontend (React + TypeScript via Vite — já escafoldado, protótipo visual dos 5 passos
da Tela 1, com dados mockados; ver [`frontend/README.md`](frontend/README.md)):

```bash
cd modulos/inscricao/frontend
npm install
npm run dev
```
