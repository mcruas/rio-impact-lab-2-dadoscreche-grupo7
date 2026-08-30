"""Tabela de referência por CEP: onde fica o CEP e quais escolas ficam perto dele.

Mesma divisão de responsabilidades de `app/data.py`, pelos mesmos motivos:

- `carregar_ceps()` / `carregar_cep_escolas()` (produção, inclusive Vercel): leem
  `dados/ceps.csv` e `dados/cep_escolas.csv`, já processados e commitados no git.
  Só usam a stdlib — nada de DuckDB, de `desafio/` ou de rede em runtime.
- `recalcular_de_desafio()` (local, com `desafio/` presente): recalcula tudo do zero
  e é o que `scripts/gerar_ceps.py` grava nos dois CSVs acima. Rodar de novo sempre
  que os dados de `desafio/` mudarem.

Por que precomputar: a localização de um CEP é um fato estável, não algo a recalcular
por request. Antes desta tabela o módulo resolvia CEP -> bairro chamando o ViaCEP pela
rede (ver `app/cep.py`) e aproximava a posição da família pelo centróide das escolas do
bairro informado (ver `app/distancia.py`) — uma aproximação circular ("onde há escolas")
e grosseira.

De onde saem as coordenadas, sem nenhuma API externa:
`desafio/Bases IC_ ClassificadoseFila/04_UnidadesEscolaresComEndereco.csv` (Query D)
tem o **CEP de cada escola**, e `dados/escolas.duckdb` tem a lat/long exata dessa mesma
escola. Casando os dois sobram ~1.913 âncoras (CEP real -> coordenada real) cobrindo
353 prefixos de 5 dígitos. Como o CEP brasileiro é hierárquico e geograficamente
ordenado, essas âncoras resolvem por prefixo a grande maioria dos CEPs das famílias.

Cascata de resolução, registrada por CEP na coluna `origem_coord` (permite auditar e
filtrar por precisão):

| origem_coord | regra                                   | % da demanda coberta |
| ------------ | --------------------------------------- | -------------------- |
| `cep_exato`  | CEP idêntico ao de alguma escola        |                      |
| `prefixo5`   | centróide das âncoras do prefixo de 5   | 97,2% (acumulado)    |
| `prefixo3`   | centróide das âncoras do prefixo de 3   | 99,3% (acumulado)    |
| `bairro`     | centróide das escolas do bairro         | ~100%                |

Erro medido por leave-one-out sobre as 1.858 escolas que têm CEP e coordenada: mediana
0,65 km e p90 1,73 km, contra 0,97 km / 3,14 km do centróide de bairro usado antes.

A BrasilAPI foi testada como fonte de coordenada e **descartada**: numa amostra de 120
CEPs, 77% devolveram a sentinela `-22.90642,-43.18223` (centro do Rio) em vez da
coordenada real — Copacabana, Ramos, Inhaúma e Camorim vieram todos no mesmo ponto.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

MODULO_ROOT = Path(__file__).resolve().parents[1]
CEPS_CSV = MODULO_ROOT / "dados" / "ceps.csv"
CEP_ESCOLAS_CSV = MODULO_ROOT / "dados" / "cep_escolas.csv"

ORIGENS_COORD = ("cep_exato", "prefixo5", "prefixo3", "bairro")
VIZINHAS_POR_CEP = 10
"""Quantas escolas mais próximas guardar por CEP em dados/cep_escolas.csv."""


@dataclass(frozen=True)
class RegistroCep:
    cep: str
    """8 dígitos, sem hífen — mesmo formato de contracts/schemas/endereco.schema.json."""
    bairro: str
    """Bairro por voto majoritário entre as inscrições daquele CEP na Query A, na
    grafia apresentável do catálogo de escolas ('Campo Grande', não 'CAMPO GRANDE').
    Quem for comparar deve normalizar dos dois lados, como `data.buscar_por_bairro`
    e `distancia.distancia_mais_proxima` já fazem."""
    latitude: float
    longitude: float
    origem_coord: str
    """Qual regra da cascata resolveu a coordenada — ver ORIGENS_COORD."""
    cod_territ: str | None
    cre: int | None
    """Microárea/CRE (SME) que contém a coordenada do CEP — ver app/microarea.py.
    None quando o ponto cai fora dos polígonos mapeados."""
    n_inscricoes: int
    """Quantas inscrições da Query A vieram deste CEP. Serve de peso ao avaliar
    cobertura: um CEP raro errado pesa menos que um CEP de alta demanda errado."""


@dataclass(frozen=True)
class VizinhaCep:
    esc_codigo: str
    """No mesmo formato de dados/escolas.duckdb (sem zero à esquerda), para juntar
    direto com o catálogo que app/data.py já carrega."""
    ordem: int
    """1 = escola mais próxima deste CEP."""
    distancia_km: float
    mesma_microarea: bool
    """True quando a escola está na mesma microárea SME do CEP."""


def normalizar_cep(cep: str | None) -> str | None:
    """'23050-300' -> '23050300'. Devolve None se não sobrarem exatamente 8 dígitos."""
    if not cep:
        return None
    digitos = "".join(c for c in cep if c.isdigit())
    return digitos if len(digitos) == 8 else None


def carregar_ceps() -> dict[str, RegistroCep]:
    """Lê dados/ceps.csv. Devolve {} se o arquivo ainda não foi gerado."""
    if not CEPS_CSV.exists():
        return {}

    registros: dict[str, RegistroCep] = {}
    with CEPS_CSV.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            registros[linha["cep"]] = RegistroCep(
                cep=linha["cep"],
                bairro=linha["bairro"],
                latitude=float(linha["latitude"]),
                longitude=float(linha["longitude"]),
                origem_coord=linha["origem_coord"],
                cod_territ=linha["cod_territ"] or None,
                cre=int(linha["cre"]) if linha["cre"] else None,
                n_inscricoes=int(linha["n_inscricoes"]),
            )
    return registros


def carregar_cep_escolas() -> dict[str, list[VizinhaCep]]:
    """Lê dados/cep_escolas.csv. Cada lista já vem ordenada por proximidade."""
    if not CEP_ESCOLAS_CSV.exists():
        return {}

    vizinhas: dict[str, list[VizinhaCep]] = defaultdict(list)
    with CEP_ESCOLAS_CSV.open(encoding="utf-8", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            vizinhas[linha["cep"]].append(
                VizinhaCep(
                    esc_codigo=linha["esc_codigo"],
                    ordem=int(linha["ordem"]),
                    distancia_km=float(linha["distancia_km"]),
                    mesma_microarea=linha["mesma_microarea"] == "true",
                )
            )
    for lista in vizinhas.values():
        lista.sort(key=lambda v: v.ordem)
    return dict(vizinhas)


@lru_cache(maxsize=1)
def tabela_ceps() -> dict[str, RegistroCep]:
    """carregar_ceps() memoizado — a tabela é imutável, ler o CSV uma vez basta.

    O cache fica aqui, e não em main.py (como o de escolas), porque dois consumidores
    precisam da mesma tabela: `app/cep.py` (GET /cep/{cep}) e `app/main.py` (_rankear).
    """
    return carregar_ceps()


@lru_cache(maxsize=1)
def tabela_cep_escolas() -> dict[str, list[VizinhaCep]]:
    """carregar_cep_escolas() memoizado — ver tabela_ceps()."""
    return carregar_cep_escolas()


# ---------------------------------------------------------------------------
# Daqui para baixo: só o gerador (scripts/gerar_ceps.py), nunca o runtime.
# Exige desafio/ presente, dados/escolas.duckdb já gerado e as extensões
# excel/spatial do DuckDB — nada disso existe em produção.
# ---------------------------------------------------------------------------


def _votar_bairro(pares: list[tuple[str, int]]) -> str:
    """Bairro majoritário de um CEP. Desempate pelo nome, para o CSV ser determinístico.

    Um mesmo CEP aparece com mais de um bairro na Query A (2.587 dos 21.688), quase
    sempre por variação de grafia, mas às vezes por divisa real — ex.: 22775150 traz
    JACAREPAGUA 233x, BARRA OLIMPICA 55x e CURICICA 5x. O voto majoritário resolve.
    """
    return max(pares, key=lambda par: (par[1], par[0]))[0]


def _centroide(pontos: list[tuple[float, float]]) -> tuple[float, float]:
    return (
        sum(p[0] for p in pontos) / len(pontos),
        sum(p[1] for p in pontos) / len(pontos),
    )


def _grafias_de_exibicao(escolas) -> dict[str, str]:
    """bairro normalizado -> grafia apresentável, tirada do catálogo de escolas.

    O bairro da Query A vem sempre em CAIXA ALTA ('CAMPO GRANDE'), e devolver isso em
    `GET /cep/{cep}` pioraria o que o frontend mostra hoje. O catálogo de escolas tem as
    duas formas ('Campo Grande' e 'SANTA CRUZ'), então preferimos a grafia com minúsculas
    e, entre elas, a mais frequente. Sem nenhuma, cai para `.title()` do normalizado.
    """
    from .data import _bairro_base, _normalizar

    contagem: dict[str, Counter] = defaultdict(Counter)
    for escola in escolas:
        base = _bairro_base(escola.bairro)
        contagem[_normalizar(base)][base] += 1

    grafias = {}
    for chave, opcoes in contagem.items():
        mistas = [(n, g) for g, n in opcoes.items() if not g.isupper()]
        grafias[chave] = max(mistas)[1] if mistas else max((n, g) for g, n in opcoes.items())[1]
    return grafias


def recalcular_de_desafio() -> tuple[list[RegistroCep], list[tuple[str, VizinhaCep]]]:
    """Lê desafio/ do zero e devolve (registros por CEP, vizinhança CEP->escolas).

    Só usada por scripts/gerar_ceps.py. As duas listas saem prontas para virarem
    dados/ceps.csv e dados/cep_escolas.csv.
    """
    import duckdb

    from . import microarea
    from .data import (
        QUERY_A_DIR,
        _bairro_base,
        _normalizar,
        _resolver_query_a,
        carregar_escolas,
    )
    from .distancia import centroides_por_bairro

    query_d = QUERY_A_DIR / "04_UnidadesEscolaresComEndereco.csv"
    if not query_d.exists():
        raise FileNotFoundError(
            f"Não encontrei {query_d} — esses dados são fornecidos fora do git "
            "(ver CLAUDE.md), confirme se desafio/ está presente localmente."
        )

    escolas = carregar_escolas()
    escolas_com_coord = [e for e in escolas if e.latitude is not None and e.longitude is not None]
    coord_por_escola = {e.esc_codigo: (e.latitude, e.longitude) for e in escolas_com_coord}

    con = duckdb.connect()

    # 1. CEP -> bairro (voto majoritário) e n_inscricoes, da Query A.
    #    CEP e bairro usam o literal 'NULL' para ausente (ver CLAUDE.md), não NULL de verdade.
    pares_cep_bairro = con.execute(
        f"""
        SELECT regexp_replace(CEP, '[^0-9]', '', 'g') AS cep,
               NULLIF(bairro, 'NULL') AS bairro,
               COUNT(*) AS n
        FROM read_csv_auto('{_resolver_query_a().as_posix()}', delim=';', header=true,
                           encoding='utf-8', ignore_errors=true)
        WHERE NULLIF(CEP, 'NULL') IS NOT NULL
          AND length(regexp_replace(CEP, '[^0-9]', '', 'g')) = 8
        GROUP BY 1, 2
        """
    ).fetchall()

    votos: dict[str, list[tuple[str, int]]] = defaultdict(list)
    total_por_cep: dict[str, int] = defaultdict(int)
    for cep, bairro, n in pares_cep_bairro:
        total_por_cep[cep] += n
        if bairro:
            votos[cep].append((_normalizar(_bairro_base(bairro)), n))

    # 2. Âncoras: CEP da escola (Query D, sem cabeçalho) + coordenada real da escola.
    #    Ler com header=true engoliria a primeira unidade (ver CLAUDE.md).
    #    Aqui o código vem zero-padded e no escolas.duckdb vem sem o zero -> casar por inteiro.
    anc_raw = con.execute(
        f"""
        SELECT TRY_CAST(column1 AS BIGINT) AS esc_num,
               regexp_replace(NULLIF(column8, 'NULL'), '[^0-9]', '', 'g') AS cep
        FROM read_csv_auto('{query_d.as_posix()}', delim=';', header=false,
                           encoding='utf-8', ignore_errors=true)
        """
    ).fetchall()

    ancoras_cep: dict[str, list[tuple[float, float]]] = defaultdict(list)
    ancoras_p5: dict[str, list[tuple[float, float]]] = defaultdict(list)
    ancoras_p3: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for esc_num, cep_escola in anc_raw:
        if esc_num is None or not cep_escola or len(cep_escola) != 8:
            continue
        coord = coord_por_escola.get(str(esc_num))
        if coord is None:
            continue
        ancoras_cep[cep_escola].append(coord)
        ancoras_p5[cep_escola[:5]].append(coord)
        ancoras_p3[cep_escola[:3]].append(coord)

    centroides_bairro = centroides_por_bairro(escolas)
    exibicao = _grafias_de_exibicao(escolas)

    # 3. Cascata de coordenada, do mais preciso ao mais grosseiro.
    resolvidos: dict[str, tuple[float, float, str, str]] = {}
    for cep in total_por_cep:
        # `norm` é a chave de comparação; `bairro` é o que vai para o CSV.
        norm = _votar_bairro(votos[cep]) if votos[cep] else ""
        bairro = exibicao.get(norm, norm.title()) if norm else ""
        for origem, pontos in (
            ("cep_exato", ancoras_cep.get(cep)),
            ("prefixo5", ancoras_p5.get(cep[:5])),
            ("prefixo3", ancoras_p3.get(cep[:3])),
        ):
            if pontos:
                lat, lon = _centroide(pontos)
                resolvidos[cep] = (lat, lon, origem, bairro)
                break
        else:
            centro = centroides_bairro.get(norm) if norm else None
            if centro is None:
                continue  # sem âncora e sem bairro reconhecido: não dá para localizar
            resolvidos[cep] = (centro[0], centro[1], "bairro", bairro)

    # 4. Microárea do CEP, por ponto-em-polígono (mesma rotina usada para as escolas).
    microarea.carregar_microareas(con)
    micro_por_cep = microarea.atribuir_microarea_lote(
        con, {cep: (lat, lon) for cep, (lat, lon, _, _) in resolvidos.items()}
    )

    registros = [
        RegistroCep(
            cep=cep,
            bairro=bairro,
            latitude=lat,
            longitude=lon,
            origem_coord=origem,
            cod_territ=micro_por_cep.get(cep, (None, None))[0],
            cre=micro_por_cep.get(cep, (None, None))[1],
            n_inscricoes=total_por_cep[cep],
        )
        for cep, (lat, lon, origem, bairro) in sorted(resolvidos.items())
    ]

    vizinhas = _vizinhas_mais_proximas(con, registros, escolas_com_coord)
    con.close()
    return registros, vizinhas


def _vizinhas_mais_proximas(con, registros, escolas) -> list[tuple[str, VizinhaCep]]:
    """As VIZINHAS_POR_CEP escolas mais próximas de cada CEP.

    ~21,7k CEPs x 1,9k escolas = 42M pares: em DuckDB isso roda em segundos, em
    Python puro levaria minutos. Devolve pares (cep, VizinhaCep) já ordenados.
    """
    con.execute("CREATE OR REPLACE TABLE _ceps (cep VARCHAR, lat DOUBLE, lon DOUBLE, ct VARCHAR)")
    con.executemany(
        "INSERT INTO _ceps VALUES (?, ?, ?, ?)",
        [(r.cep, r.latitude, r.longitude, r.cod_territ) for r in registros],
    )
    con.execute("CREATE OR REPLACE TABLE _esc (cod VARCHAR, lat DOUBLE, lon DOUBLE, ct VARCHAR)")
    con.executemany(
        "INSERT INTO _esc VALUES (?, ?, ?, ?)",
        [(e.esc_codigo, e.latitude, e.longitude, e.cod_territ) for e in escolas],
    )
    # Mesma fórmula de distancia.haversine_km, aqui em SQL para rodar os 42M pares em lote.
    con.execute(
        """
        CREATE OR REPLACE MACRO _hav(a1, o1, a2, o2) AS 6371.0 * 2 * asin(sqrt(
            pow(sin(radians(a2 - a1) / 2), 2)
            + cos(radians(a1)) * cos(radians(a2)) * pow(sin(radians(o2 - o1) / 2), 2)))
        """
    )
    linhas = con.execute(
        f"""
        SELECT cep, cod, ordem, dist, mesma
        FROM (
            SELECT c.cep AS cep, e.cod AS cod,
                   _hav(c.lat, c.lon, e.lat, e.lon) AS dist,
                   (c.ct IS NOT NULL AND c.ct = e.ct) AS mesma,
                   row_number() OVER (PARTITION BY c.cep
                                      ORDER BY _hav(c.lat, c.lon, e.lat, e.lon), e.cod) AS ordem
            FROM _ceps c CROSS JOIN _esc e
        )
        WHERE ordem <= {VIZINHAS_POR_CEP}
        ORDER BY cep, ordem
        """
    ).fetchall()
    con.execute("DROP TABLE _ceps")
    con.execute("DROP TABLE _esc")
    return [
        (
            cep,
            VizinhaCep(
                esc_codigo=cod,
                ordem=ordem,
                distancia_km=dist,
                mesma_microarea=bool(mesma),
            ),
        )
        for cep, cod, ordem, dist, mesma in linhas
    ]
