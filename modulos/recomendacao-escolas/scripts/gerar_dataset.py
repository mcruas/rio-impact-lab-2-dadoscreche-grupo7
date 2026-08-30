"""Gera dados/escolas.duckdb a partir de desafio/ (join completo + microárea).

Rodar a partir de modulos/recomendacao-escolas/, com desafio/ presente:
    python scripts/gerar_dataset.py

O arquivo gerado (~1941 linhas, poucas centenas de KB) é commitado no git e é
o que o app lê por padrão (app/data.py::carregar_escolas) — sem ele, rodar em
produção/deploy (ex.: Vercel) exigiria ter desafio/ e as extensões
excel/spatial do DuckDB disponíveis em runtime, o que não é o caso.

Regenerar sempre que os dados de desafio/ mudarem (ex.: nova exportação de
Unidades_Unificadas_com_Localizacao.xlsx ou de Query A).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import duckdb  # noqa: E402

from app.data import DATASET_PRECOMPUTADO, recalcular_de_desafio  # noqa: E402


def main() -> None:
    escolas = recalcular_de_desafio()

    DATASET_PRECOMPUTADO.parent.mkdir(parents=True, exist_ok=True)
    if DATASET_PRECOMPUTADO.exists():
        DATASET_PRECOMPUTADO.unlink()

    con = duckdb.connect(str(DATASET_PRECOMPUTADO))
    con.execute(
        """
        CREATE TABLE escolas (
            esc_codigo VARCHAR,
            nome VARCHAR,
            endereco VARCHAR,
            bairro VARCHAR,
            latitude DOUBLE,
            longitude DOUBLE,
            tipo VARCHAR,
            indice_concorrencia DOUBLE,
            cod_territ VARCHAR,
            cre INTEGER
        )
        """
    )
    con.executemany(
        "INSERT INTO escolas VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                e.esc_codigo,
                e.nome,
                e.endereco,
                e.bairro,
                e.latitude,
                e.longitude,
                e.tipo,
                e.indice_concorrencia,
                e.cod_territ,
                e.cre,
            )
            for e in escolas
        ],
    )
    con.close()
    print(f"OK: {len(escolas)} escolas gravadas em {DATASET_PRECOMPUTADO}")


if __name__ == "__main__":
    main()
