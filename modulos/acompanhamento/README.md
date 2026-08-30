# Acompanhamento (Tela 3 + Eixo 3)

> Implementado. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md) para a visão
> geral do sistema e [`../../INTEGRACAO_RMI_WHATSAPP.md`](../../INTEGRACAO_RMI_WHATSAPP.md)
> para o fluxo completo de convocação (por que a cascata de telefones existe,
> por que a confirmação pede dígitos de CPF, o que é real vs. simulado neste
> hackathon).

## Responsabilidade

Duas coisas:

1. **Tela 3** — o responsável busca, por CPF (da criança ou dele mesmo), o
   lugar na fila da inscrição. Camada fina — não possui dados próprios, só
   repassa o status do `match-engine/`.
2. **Eixo 3 (convocação)** — dono do contato automatizado via WhatsApp/RMI que
   pede ao responsável para confirmar uma vaga que o Motor de Match alocou.
   Máquina de estados própria (`AguardandoResposta` → `Confirmada`,
   `EsgotadoEscalarManual` ou `Liberada`), guardada em memória, implementada
   em [`backend/ciclo_convocacao.py`](backend/ciclo_convocacao.py) — `main.py`
   só traduz HTTP para essas funções, de propósito, para a lógica de negócio
   não ficar misturada com a camada de rotas.

Contrato: [`../../contracts/acompanhamento.openapi.yaml`](../../contracts/acompanhamento.openapi.yaml).

## O que este módulo consome

- [`match-engine.openapi.yaml`](../../contracts/match-engine.openapi.yaml)
  (`GET /status/{cpf}`, `POST /nao-confirmados`)

**Só por contrato** — nunca acessar o banco/código interno de `match-engine/` diretamente.

## O que este módulo expõe

- `GET /acompanhamento/{cpf}` — repassa o status consultado no Motor de Match.
- `POST /convocacoes/{cpf}` — dispara (ou reconsulta) a convocação de uma
  criança com vaga `Confirmada`; `409` se ainda não tem vaga.
- `GET /convocacoes/{cpf}` — estado atual da convocação.
- `POST /convocacoes/{cpf}/eventos` — webhook para o LLM do WhatsApp da
  Prefeitura reportar a intenção estruturada extraída da resposta do
  responsável (`confirmar` com dígitos de CPF, ou `nao_sou_eu`).
- `POST /convocacoes/verificar-prazos` — avança quem estourou o prazo de
  resposta por silêncio, e libera (chamando o Motor de Match em lote) quem
  estourou também o prazo do fluxo manual do diretor. Em produção roda numa
  tarefa periódica; aqui é disparável sob demanda para poder demonstrar o
  ciclo completo sem esperar os prazos reais passarem.

## Limitações conhecidas (simulado neste hackathon)

A base anonimizada não tem CPF nem telefone reais, então dois pedaços são
mock — o resto (contrato, máquina de estados, verificação, e o recálculo real
do Motor de Match ao liberar uma vaga) é o que valeria em produção. Detalhes e
porquês em [`../../INTEGRACAO_RMI_WHATSAPP.md`](../../INTEGRACAO_RMI_WHATSAPP.md):

- Cascata de telefones do RMI: tamanho fixo (3), não a lista real por pessoa.
- Autenticação por "últimos 4 dígitos do CPF": gerada por hash do código
  anonimizado, não dígitos de CPF de verdade.
- `POST /convocacoes/verificar-prazos` é disparado manualmente, não por uma
  tarefa agendada (não há orquestrador tipo cron/Prefect neste hackathon).

## Como começar

```bash
cd modulos/acompanhamento/backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
MATCH_ENGINE_URL=http://127.0.0.1:8001 uvicorn main:app --reload --port 8002
```

Requer o Motor de Match rodando (ver
[`../match-engine/README.md`](../match-engine/README.md)) — este módulo só o
consulta por HTTP, nunca acessa `motor.py` diretamente.

Frontend (React + TypeScript, ainda não escafoldado):

```bash
cd modulos/acompanhamento/frontend
npm create vite@latest . -- --template react-ts
```
