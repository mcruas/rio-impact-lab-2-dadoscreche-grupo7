# Inscrição (Tela 1)

> Módulo esqueleto — implementação a fazer. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura/qualidade.

## Responsabilidade

Dono da entidade `Inscricao` (contrato: [`../../contracts/inscricao.openapi.yaml`](../../contracts/inscricao.openapi.yaml)).
Tela de formulário onde o responsável cadastra:

- Nome da criança, CPF da criança, CPF do responsável, data de nascimento da criança
- Turno: Integral ou Parcial
- Até 3 endereços de interesse
- Até 5 escolas escolhidas (a partir da lista/mapa trazida pelo módulo Recomendação de Escola)

## O que este módulo consome

- [`recomendacao-escolas.openapi.yaml`](../../contracts/recomendacao-escolas.openapi.yaml)
  (`GET /escolas?bairro=`) — para listar/mapear escolas da região de cada endereço de
  interesse e deixar o responsável escolher até 5, exibindo a tag de priorização.

**Só por contrato** — nunca acessar o banco/código interno de `recomendacao-escolas/`
diretamente.

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

Frontend (React + TypeScript, ainda não escafoldado):

```bash
cd modulos/inscricao/frontend
npm create vite@latest . -- --template react-ts
```
