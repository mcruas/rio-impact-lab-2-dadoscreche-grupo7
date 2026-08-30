"""Atribuição de microárea SME (Territórios_SME) a partir de latitude/longitude.

Fonte: desafio/Microáreas_SME_revisãoIPP/Microareas_SME_revisao.shp — 233 polígonos
(campo cod_territ), agrupados em 11 CREs (campo cre). Sem nome de bairro no shapefile:
a atribuição só é possível por coordenada real (ponto-em-polígono), nunca por texto de
bairro — um polígono chega a cobrir vários nomes de bairro distintos.

Lido via extensão `spatial` do DuckDB (mesma dependência já usada por data.py para o
Excel; nenhuma lib nova). O shapefile está em SIRGAS 2000 / UTM 23S (EPSG:31983,
metros); nossas coordenadas de escola/família são WGS84 (EPSG:4326, graus).

Pegadinha real do ST_Transform do DuckDB: por padrão ele assume ordem de eixo
(latitude, longitude) para EPSG:4326 (convenção oficial do EPSG), não (longitude,
latitude). Passar lon/lat na ordem "óbvia" sem `always_xy := true` transforma o ponto
silenciosamente (sem erro) para uma posição a centenas de km de distância. Sempre usar
`always_xy := true` com ST_Point(longitude, latitude).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[3]
MICROAREAS_SHP = (
    REPO_ROOT / "desafio" / "Microáreas_SME_revisãoIPP" / "Microareas_SME_revisao.shp"
)

WGS84 = "EPSG:4326"
SIRGAS2000_UTM23S = "EPSG:31983"


def _checar_shapefile() -> None:
    if not MICROAREAS_SHP.exists():
        raise FileNotFoundError(
            f"Não encontrei {MICROAREAS_SHP} — esses dados são fornecidos fora do git "
            "(ver CLAUDE.md), confirme se desafio/ está presente localmente."
        )


def carregar_microareas(con: duckdb.DuckDBPyConnection) -> None:
    """Cria a tabela `microareas` na conexão dada (idempotente por conexão)."""
    _checar_shapefile()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(
        f"""
        CREATE OR REPLACE TABLE microareas AS
        SELECT cod_territ, cre, st_area_sh / 1e6 AS area_km2, geom
        FROM st_read('{MICROAREAS_SHP.as_posix()}')
        """
    )


def atribuir_microarea_lote(
    con: duckdb.DuckDBPyConnection, pontos: dict[str, tuple[float, float]]
) -> dict[str, tuple[str, int]]:
    """pontos: chave -> (latitude, longitude). Devolve chave -> (cod_territ, cre).

    Só inclui no resultado as chaves cujo ponto caiu dentro de alguma microárea —
    chaves sem lat/long válida ou fora de todos os polígonos (ex.: fora do
    município) ficam ausentes. Requer que carregar_microareas() já tenha rodado
    nesta conexão.
    """
    if not pontos:
        return {}

    con.execute("CREATE OR REPLACE TABLE _pontos (chave VARCHAR, lat DOUBLE, lon DOUBLE)")
    con.executemany(
        "INSERT INTO _pontos VALUES (?, ?, ?)",
        [(chave, lat, lon) for chave, (lat, lon) in pontos.items()],
    )

    resultado = con.execute(
        f"""
        SELECT p.chave, m.cod_territ, m.cre
        FROM _pontos p
        JOIN microareas m
          ON ST_Contains(
               m.geom,
               ST_Transform(ST_Point(p.lon, p.lat), '{WGS84}', '{SIRGAS2000_UTM23S}', always_xy := true)
             )
        """
    ).fetchall()
    con.execute("DROP TABLE _pontos")
    return {chave: (cod_territ, cre) for chave, cod_territ, cre in resultado}


def atribuir_microarea(
    con: duckdb.DuckDBPyConnection, latitude: float, longitude: float
) -> tuple[str, int] | None:
    """Atribuição pontual (ex.: endereço de uma família em tempo de requisição).

    Requer que carregar_microareas() já tenha rodado nesta conexão.
    """
    resultado = con.execute(
        f"""
        SELECT cod_territ, cre
        FROM microareas
        WHERE ST_Contains(
                geom,
                ST_Transform(ST_Point($lon, $lat), '{WGS84}', '{SIRGAS2000_UTM23S}', always_xy := true)
              )
        LIMIT 1
        """,
        {"lon": longitude, "lat": latitude},
    ).fetchone()
    return (resultado[0], resultado[1]) if resultado is not None else None
