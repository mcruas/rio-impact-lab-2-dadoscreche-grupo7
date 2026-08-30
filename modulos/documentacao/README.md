# Documentação (Tela 2)

> Módulo esqueleto — implementação a fazer. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura/qualidade.

## Responsabilidade

Dono da entidade `Documento` (contrato: [`../../contracts/documentacao.openapi.yaml`](../../contracts/documentacao.openapi.yaml)).
Tela onde o responsável envia, para uma inscrição já existente:

- RG e CPF do responsável, Certidão de Nascimento, CPF e RG da criança
- Carteira de Vacinação, Cartão do SUS
- Foto 3x4 recente da criança

## O que este módulo consome

- [`inscricao.openapi.yaml`](../../contracts/inscricao.openapi.yaml) (`GET /inscricoes/{cpf}`) —
  para confirmar que existe uma inscrição antes de aceitar documentos, e para exibir o
  contexto da criança na tela.

**Só por contrato** — nunca acessar o banco/código interno de `inscricao/` diretamente.

## O que este módulo expõe

- `POST /documentos` — registra o envio de um documento para uma inscrição.
- `GET /documentos?inscricao_id=` — consultado pelo `match-engine/` para saber quais
  documentos já foram validados antes de calcular a pontuação.

## Como começar

```bash
cd modulos/documentacao/backend
python -m venv .venv && source .venv/Scripts/activate
pip install fastapi "uvicorn[standard]" pydantic
uvicorn main:app --reload
```

Frontend (React + TypeScript, ainda não escafoldado):

```bash
cd modulos/documentacao/frontend
npm create vite@latest . -- --template react-ts
```
