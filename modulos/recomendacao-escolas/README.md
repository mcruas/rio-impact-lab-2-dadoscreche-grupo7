# Recomendação de Escola

Backend consumido pela Tela 1 (Inscrição): dado um bairro de interesse, devolve as
escolas da região com uma **tag de priorização** (`Alta`/`Média`/`Baixa`/`Sem dado`).
Contrato público em [`../../contracts/recomendacao-escolas.openapi.yaml`](../../contracts/recomendacao-escolas.openapi.yaml).

Este é o **módulo de referência** da arquitetura (ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)):
totalmente implementado, para servir de modelo de estrutura/qualidade para os demais.

## Como funciona

- Lê `desafio/OferecimentosEvagas/Unidades_Unificadas_com_Localizacao.xlsx` (endereço,
  bairro, latitude/longitude e tipo de cada unidade) via DuckDB (`INSTALL/LOAD excel`).
- Cruza com `desafio/Bases IC_ ClassificadoseFila/01_QueryA_InscricoesPorAno.csv(.gz)`
  para estimar, por unidade, a proporção histórica de inscrições que terminaram
  atendidas (`Confirmado`/`Ativo`/`Selecionado`/`Selecionado da lista`) — essa
  proporção vira a tag de priorização (`>=0.6` Alta, `>=0.3` Média, `<0.3` Baixa,
  sem histórico na base = "Sem dado").
- **Isso é uma heurística ilustrativa**, não uma recomendação real: os dados de
  `desafio/` são anonimizados (ver `CLAUDE.md`), e a tag não representa a chance
  real de uma criança conseguir vaga.
- Não depende de nenhum outro módulo de `modulos/` — só dos dados de `desafio/`.

### Achado de qualidade de dado (documentado em `app/data.py`)

`BAIRRO` em `Unidades_Unificadas_com_Localizacao.xlsx` tem ~323 valores distintos
para bem menos bairros reais (mesma unidade com bairro em MAIÚSCULO e Title Case,
sufixos tipo "Andaraí - Jamelão"). A busca normaliza (sem acento, maiúsculo, corta
sufixo após " - "/" (") antes de comparar — mas variantes sem esse padrão (ex.:
"Alto da Boa Vista" vs "Alto Boa Vista") continuam sendo bairros diferentes.

## Rodar localmente

Requer `desafio/` presente no repo (dados fornecidos fora do git — ver `CLAUDE.md`
e o `.gitignore` da raiz).

```bash
cd modulos/recomendacao-escolas
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; no PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Testar:

```bash
curl "http://127.0.0.1:8000/escolas?bairro=Tijuca"
```

## Testes

```bash
pytest tests
```
