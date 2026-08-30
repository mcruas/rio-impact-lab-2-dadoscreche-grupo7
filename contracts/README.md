# Contratos entre módulos

Este diretório é a **única fonte da verdade** sobre como os 5 módulos de `modulos/` se
comunicam. Nenhum módulo deve depender do código interno de outro — só do que está
definido aqui. É isso que permite implementar, testar e auditar cada módulo de forma
independente (ver [`../ARQUITETURA.md`](../ARQUITETURA.md) para a visão geral do sistema).

## O que tem aqui

- `schemas/*.schema.json` — JSON Schema (draft 2020-12) das entidades de dados
  compartilhadas entre módulos: `crianca`, `responsavel`, `endereco`, `inscricao`,
  `escola`, `documento`, `criterio_match`, `status_fila`.
- `<modulo>.openapi.yaml` — contrato REST público de cada módulo (OpenAPI 3.0),
  referenciando os schemas acima via `$ref`. Um arquivo por módulo, mesmo nome da
  pasta em `modulos/`.
- `validate_contracts.py` — valida que todos os `.openapi.yaml` e `.schema.json` são
  bem formados. Não valida a implementação de nenhum módulo, só os contratos em si.

## Regra de mudança

Qualquer alteração num contrato (adicionar/remover campo, mudar tipo, mudar enum, etc.)
precisa ser combinada entre quem implementa o módulo dono do contrato e quem implementa
qualquer módulo que o consome — nunca mudar unilateralmente. Ao alterar um contrato,
rode `validate_contracts.py` antes de abrir PR.

## Como validar

```bash
pip install -r ../modulos/recomendacao-escolas/requirements.txt  # ou instale só as libs de validação:
pip install pyyaml jsonschema openapi-spec-validator
python validate_contracts.py
```

## Quem consome o quê

| Módulo | Contrato próprio | Contratos que consome |
| --- | --- | --- |
| `inscricao` (Tela 1) | `inscricao.openapi.yaml` | `recomendacao-escolas.openapi.yaml` |
| `recomendacao-escolas` | `recomendacao-escolas.openapi.yaml` | nenhum (só lê `desafio/`) |
| `documentacao` (Tela 2) | `documentacao.openapi.yaml` | `inscricao.openapi.yaml` |
| `match-engine` | `match-engine.openapi.yaml` | `inscricao.openapi.yaml`, `documentacao.openapi.yaml` |
| `acompanhamento` (Tela 3) | `acompanhamento.openapi.yaml` | `match-engine.openapi.yaml` |
