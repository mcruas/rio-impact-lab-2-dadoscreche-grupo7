# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is the repository for **this group's solution** to the "Claude Impact Lab 2026" hackathon challenge on Rio de Janeiro's public daycare (creche) enrollment system. It is split into three parts:

- **`desafio/`** — the standard challenge material, identical across all groups (original challenge `README.md`, briefing/presentation, and all anonymized datasets from the Secretaria Municipal de Educação, SME). Treat this as read-only reference input, not something to edit.
- **`eda/`** — this group's own exploratory data analysis: hypotheses, findings, and the reproducible DuckDB script behind them.
- **Repository root** — where this group's actual solution (whatever it ends up being: app, model, report, etc.) will live going forward.

**All data in `desafio/` is anonymized and does not represent real-world figures.** Indicators computed from it should never be presented as reflecting reality — this is emphasized in `desafio/README.md` and should carry through to any analysis or report generated from these files.

## `desafio/` — dataset layout

| Folder/file | Contents |
| --- | --- |
| `desafio/Bases IC_ ClassificadoseFila/` | Core creche enrollment/classification/waitlist data (Queries A–D). See dictionary below. |
| `desafio/OferecimentosEvagas/` | Monthly enrollment monitoring for partner (conveniada) and public daycare units, 2021–2025, plus a unified units-with-location file. See `LEIAME_OFERECIMENTOSPARCEIRASEPUBLICAS.txt` for provenance/cadence details. |
| `desafio/Microáreas_SME_revisãoIPP/` | Shapefile set (`.shp`/`.dbf`/`.shx`/etc.) for territorial micro-area maps used by SME. |
| `desafio/NascidosvivosRJ.xlsx` | Live births in the municipality — reference for potential demand. |
| `desafio/Apresentação-problema.pdf`, `desafio/Briefing_problema.docx` | Challenge presentation and briefing documents. |

The full data dictionary (schemas, join keys, known data-quality issues) lives in `desafio/README.md` and `desafio/Bases IC_ ClassificadoseFila/README_dicionario_dados.md` — read those before writing any analysis code rather than inferring schema from a raw file peek, since several columns have non-obvious meaning or encoding quirks (see below).

### Query A–D relationships (`desafio/Bases IC_ ClassificadoseFila/`)

- **Query A** (`01_QueryA_InscricoesPorAno.csv.gz`): one row per chosen daycare option within an enrollment. Joins to **Query B** on `(prm_id, plm_id, ipl_id)`, and to **Query D** via `unidade` = `esc_codigo`.
- **Query B** (`02_QueryB_RespostasSocioEconomicas.csv.gz`): one row per answered classification question (long format). `ich_perg_id` joins to **Query C**.
- **Query C** (`03_QueryC_PerguntasComDescricao.csv`): catalog of questions and their scoring weights (`perg_pontuacao`) per year/process.
- **Query D** (`04_UnidadesEscolaresComEndereco.csv`): school unit addresses.

### Critical gotchas when working with this data

- **`02_QueryB_RespostasSocioEconomicas.csv.gz` does not fit in Excel** (4.36M rows > Excel's 1,048,576 row limit) and needs several GB of RAM if loaded fully. Read it in chunks (`pd.read_csv(..., chunksize=...)`) or use DuckDB, which can query the `.gz` directly without loading it fully into memory.
- Both large CSVs are `.gz`-compressed only because GitHub rejects files over 100 MB — content is byte-identical to the uncompressed CSV. Most tools (pandas, R, DuckDB) can read `.csv.gz` directly without decompressing.
- All CSVs use `;` as the separator and UTF-8 **with BOM** encoding (`encoding="utf-8-sig"` in pandas).
- `04_UnidadesEscolaresComEndereco.csv` has **no header row** — read with `header=None` and supply column names manually, or you silently lose the first unit and get garbage column names. Missing values are the literal string `"NULL"`.
- The `situacao` column in Query A is **not pre-filtered** — cancellations (`Cancelado pelo sistema`, `Cancelado na confirmacao`, `Cancelado`) make up over half the rows. Always filter deliberately based on the analysis question. Note `Cancelado na confirmacao` is spelled without cedilla/tilde in the actual data.
- The scoring rubric in Query C **changed materially between 2023 and 2024** — only 3 of 2023's 13 questions carried into 2024, and weights were rescaled (e.g. `perg_id = 2`, disability status, went from 100 points to 25). Don't build a time series across this boundary without normalizing for the rubric change.
- `pergunta_legenda` is empty (100% null) in both Query B and Query C — use `pergunta_texto` instead.
- **`CEP` and `bairro` in Query A also use the literal string `"NULL"` for missing values** (same convention as Query D), not a true empty CSV field. `read_csv_auto`/`pd.read_csv` will NOT treat it as null automatically — you must `NULLIF(col, 'NULL')` (SQL) or pass `na_values=["NULL"]` explicitly, or `"NULL"` silently shows up as a legitimate (and oddly frequent) neighborhood/CEP value in any groupby.
- **A small set of `aluno_anon` codes are anonymization-collision "buckets", not real children** — detect via `COUNT(DISTINCT nascimento_aluno_anomes) > 1` grouped by `aluno_anon` (~696 such codes, ~3,465 rows / 0.4% of Query A). E.g. `aluno_0000003` appears 192 times linked to 43 different birth dates and 141 different guardians — almost certainly a fallback code for records with insufficient identity data. Exclude these before any per-child analysis (reappearance across years, multiple enrollments, etc.) or it produces wildly wrong per-child aggregates.
- **The scoring logic in Query B/C also breaks in 2021 vs. 2022+**, independent of the documented 2023→2024 rubric change: the rate of `confirmado='Sim'` given `resposta='Sim'` is 88.9% in 2021 but only ~8-11% from 2022 onward — a change in validation process/definition, not just weights. Don't compare score-derived metrics across the 2021/2022 boundary without accounting for this. Also, points should only be counted when **both** `resposta='Sim' AND confirmado='Sim'` — using `confirmado='Sim'` alone over-counts, since `confirmado` also occurs on `resposta='Nao'` rows (meaning "the 'No' was validated", not "award the point").

## `eda/` — this group's exploratory analysis

- `eda/HIPOTESES_EDA.md` — prioritized hypotheses on allocation efficiency (territorial mismatch, funnel attrition/cancellations, scoring effectiveness).
- `eda/RESULTADOS_H6_H12.md` — findings for the two hypotheses investigated so far (funnel attrition and scoring effectiveness), including data-quality corrections applied.
- `eda/investigar_h6_h12.py` — the reproducible DuckDB script behind those findings. Run from the repo root: `python eda/investigar_h6_h12.py`. DuckDB is the tool of choice here (installed and fast enough to join the full Query A+B+C without chunking); pandas/numpy are **not** installed in this environment.
