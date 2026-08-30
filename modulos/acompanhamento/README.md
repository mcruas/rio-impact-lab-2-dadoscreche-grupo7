# Acompanhamento (Tela 3)

> Módulo esqueleto — implementação a fazer. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura/qualidade.

## Responsabilidade

Tela onde o responsável busca, por CPF (da criança ou dele mesmo), o lugar na fila da
inscrição. Camada fina — não possui dados próprios, só repassa o status do
`match-engine/`. Contrato: [`../../contracts/acompanhamento.openapi.yaml`](../../contracts/acompanhamento.openapi.yaml).

## O que este módulo consome

- [`match-engine.openapi.yaml`](../../contracts/match-engine.openapi.yaml) (`GET /status/{cpf}`)

**Só por contrato** — nunca acessar o banco/código interno de `match-engine/` diretamente.

## O que este módulo expõe

- `GET /acompanhamento/{cpf}` — repassa o status consultado no Motor de Match.

## Como começar

```bash
cd modulos/acompanhamento/backend
python -m venv .venv && source .venv/Scripts/activate
pip install fastapi "uvicorn[standard]" pydantic httpx
uvicorn main:app --reload
```

Frontend (React + TypeScript, ainda não escafoldado):

```bash
cd modulos/acompanhamento/frontend
npm create vite@latest . -- --template react-ts
```
