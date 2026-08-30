# Arquitetura da solução

Ponto de entrada único para quem vai implementar um dos módulos do sistema de
inscrição em creche. Leia isto antes de começar seu componente.

## Módulos

O time está dividido em **5 componentes independentes**, cada um em sua própria pasta
dentro de `modulos/`. Cada tela (1, 2, 3) é, na prática, um par frontend+backend
próprio — o backend dela é dono dos dados daquela etapa. Os dois módulos
"backend puro" (Recomendação de Escola, Motor de Match) são serviços à parte,
consumidos via API pelas telas.

| Pasta | Componente | Dono de quê |
| --- | --- | --- |
| [`modulos/inscricao/`](modulos/inscricao/) | Tela 1 — Inscrição | Entidade `Inscricao` (criança, responsável, endereços, escolas escolhidas) |
| [`modulos/recomendacao-escolas/`](modulos/recomendacao-escolas/) | Backend — Recomendação de Escola | Lista/mapa de escolas por bairro, com tag de priorização — **implementado, use como referência** |
| [`modulos/documentacao/`](modulos/documentacao/) | Tela 2 — Documentação | Entidade `Documento` |
| [`modulos/match-engine/`](modulos/match-engine/) | Backend — Motor de Match | Critérios de pontuação e posição na fila |
| [`modulos/acompanhamento/`](modulos/acompanhamento/) | Tela 3 — Acompanhamento | Consulta de status por CPF (sem dados próprios) |

## Regra de ouro: contratos, não código

Nenhum módulo deve importar ou depender do código interno de outro. A única forma de
comunicação entre módulos é via API HTTP, e a única fonte da verdade sobre essa API
é [`contracts/`](contracts/) — schemas de dados (`contracts/schemas/*.schema.json`) e
especificação REST (`contracts/<modulo>.openapi.yaml`) de cada módulo. Isso é o que
garante que cada componente possa ser **implementado, testado e auditado de forma
independente** pelo integrante responsável, sem precisar entender os outros quatro.

Antes de mudar um contrato, combine com quem implementa o módulo do outro lado. Para
validar que os contratos continuam bem formados: `python contracts/validate_contracts.py`
(ver [`contracts/README.md`](contracts/README.md)).

## Fluxo de dados

```
Tela 1 --POST /score-preliminar, GET /historico/{cpf}--> Motor de Match (score/histórico, se já existirem
                                                            — endpoints propostos, ainda não implementados;
                                                            recomendacao-escolas já funciona sem eles)
Tela 1 (Inscrição) --POST /recomendacoes--> Recomendação de Escola --escolas + racional--> Tela 1
Tela 1             --POST /inscricoes-------> [backend Inscrição]  (persiste a inscrição)

Tela 2 (Documentação) --GET /inscricoes/{cpf}--> [backend Inscrição]     (confirma contexto)
Tela 2                --POST /documentos-------> [backend Documentação] (envia/valida docs)

Motor de Match --GET /inscricoes/{id}--------> [backend Inscrição]
Motor de Match --GET /documentos?inscricao_id=-> [backend Documentação]
Motor de Match --calcula critérios/pontuação--> expõe GET /status/{cpf}

Tela 3 (Acompanhamento) --GET /status/{cpf}--> Motor de Match --posição na fila--> Tela 3
```

CPF (da criança, e do responsável) é a chave de busca natural entre módulos — trate
como dado sensível (não logar em texto puro), mesmo em ambiente de demonstração.

## Stack

- **Backend**: Python + FastAPI, um serviço por módulo (cada um com seu próprio
  `requirements.txt`/venv — sem dependência de código entre módulos).
- **Frontend**: React + TypeScript (Vite) para as 3 telas.
- **Persistência**: cada módulo dono de entidade (`inscricao`, `documentacao`,
  `match-engine`) escolhe seu próprio armazenamento (arquivo, SQLite, etc. — o que for
  mais rápido para o hackathon). Nunca compartilhar banco entre módulos: isso quebraria
  a separação/auditoria independente que é o requisito central desta arquitetura.

## Como começar seu módulo

1. Leia o `README.md` da sua pasta em `modulos/` — lista o que o módulo consome/expõe.
2. Leia o(s) contrato(s) relevante(s) em `contracts/`.
3. Use [`modulos/recomendacao-escolas/`](modulos/recomendacao-escolas/) como referência de
   estrutura (README, `requirements.txt`, testes, como rodar).
4. Rode `python contracts/validate_contracts.py` sempre que mexer em um contrato.

## Dados

Os módulos que leem dados do desafio (`recomendacao-escolas`, e provavelmente
`match-engine`) usam os arquivos em [`desafio/`](desafio/README.md) — ver os
cuidados de leitura documentados em [`CLAUDE.md`](CLAUDE.md) (encoding, valores
`"NULL"` literais, CSV sem header, etc.) e os achados já validados em
[`eda/RESULTADOS_H6_H12.md`](eda/RESULTADOS_H6_H12.md) antes de reimplementar lógica
parecida (ex.: régua de pontuação, taxa de atendimento).

## Integração com sistemas da Prefeitura (produção)

Para o que os módulos `documentacao` (comprovação de critérios) e `acompanhamento`/
Eixo 3 (convocação) fariam em produção, apoiados em infraestrutura que a Prefeitura já
opera (RMI, disparo de WhatsApp) em vez de sistema de notificação próprio — ver
[`INTEGRACAO_RMI_WHATSAPP.md`](INTEGRACAO_RMI_WHATSAPP.md).
