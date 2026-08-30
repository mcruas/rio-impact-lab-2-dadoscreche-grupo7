# Inscrição (Tela 1)

> Módulo esqueleto — implementação a fazer. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura/qualidade.

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

- `POST /inscricoes` — cria a inscrição (criança + responsável + endereços + escolas escolhidas).
- `GET /inscricoes/{cpf}` — consultado pelo módulo `documentacao/` para confirmar que a
  inscrição existe antes de aceitar documentos.

## Como começar

Backend (stub em `backend/main.py`):

```bash
cd modulos/inscricao/backend
python -m venv .venv && source .venv/Scripts/activate
pip install fastapi "uvicorn[standard]" pydantic
uvicorn main:app --reload
```

Frontend (React + TypeScript via Vite — já escafoldado, protótipo visual dos 5 passos
da Tela 1, com dados mockados; ver [`frontend/README.md`](frontend/README.md)):

```bash
cd modulos/inscricao/frontend
npm install
npm run dev
```
