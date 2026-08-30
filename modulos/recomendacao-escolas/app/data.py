"""Carrega e prepara os dados de escolas usados pelo endpoint /escolas.

Duas formas de carregar, para dois públicos diferentes:

- `carregar_escolas()` (usada em produção/deploy, inclusive Vercel): lê
  `dados/escolas.duckdb`, um arquivo pequeno (~1941 linhas) já processado e
  commitado no git. Rápida, não depende de `desafio/` nem das extensões
  `excel`/`spatial` do DuckDB em runtime — essencial porque o ambiente de
  deploy não tem os dados brutos do desafio (ver `.gitignore` da raiz).
- `recalcular_de_desafio()` (usada só por `scripts/gerar_dataset.py`, local,
  com `desafio/` presente): recalcula tudo do zero a partir das fontes
  originais e é o que gera o arquivo acima. Rodar de novo sempre que os dados
  de `desafio/` mudarem.

Fontes de `recalcular_de_desafio()` (lidas direto de desafio/, sem depender de
nenhum outro módulo):
- desafio/OferecimentosEvagas/Unidades_Unificadas_com_Localizacao.xlsx
  (endereço, bairro, lat/long e tipo de cada unidade — DESIGNACAO = esc_codigo).
- desafio/Bases IC_ ClassificadoseFila/01_QueryA_InscricoesPorAno.csv(.gz)
  (histórico de inscrições, só para estimar uma taxa de atendimento por unidade).

Achado de qualidade de dado (novo, não documentado em CLAUDE.md até esta etapa):
BAIRRO em Unidades_Unificadas_com_Localizacao.xlsx tem ~323 valores distintos para
bem menos bairros reais — a mesma unidade aparece com o bairro em MAIÚSCULO e em
Title Case, e variantes tipo "Andaraí - Jamelão" / "Andaraí - Morro do Andaraí"
convivem com "Andaraí" puro. A busca abaixo normaliza (maiúsculo + sem acento) e
corta qualquer sufixo depois de " - " ou " (" antes de comparar, mas variantes
sem esse padrão (ex.: "Alto da Boa Vista" vs "Alto Boa Vista") continuam sendo
tratadas como bairros diferentes — não há normalização geral confiável sem uma
tabela de referência de bairros do Rio.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from pathlib import Path

import duckdb

from . import microarea

REPO_ROOT = Path(__file__).resolve().parents[3]
MODULO_ROOT = Path(__file__).resolve().parents[1]
ESCOLAS_XLSX = (
    REPO_ROOT / "desafio" / "OferecimentosEvagas" / "Unidades_Unificadas_com_Localizacao.xlsx"
)
QUERY_A_DIR = REPO_ROOT / "desafio" / "Bases IC_ ClassificadoseFila"
DATASET_PRECOMPUTADO = MODULO_ROOT / "dados" / "escolas.duckdb"

ATENDIDA = ("Confirmado", "Ativo", "Selecionado", "Selecionado da lista")


@dataclass(frozen=True)
class Escola:
    esc_codigo: str
    nome: str
    endereco: str | None
    bairro: str
    latitude: float | None
    longitude: float | None
    tipo: str | None
    indice_concorrencia: float | None
    """1 - taxa histórica de atendimento nesta unidade (ver módulo pontuacao.py).
    None quando a unidade não tem histórico em Query A (ex.: unidade nova, ou
    conveniada que nunca apareceu como opção nos processos analisados)."""
    cod_territ: str | None = None
    cre: int | None = None
    """Microárea/CRE (SME) que contém as coordenadas da escola — ver app/microarea.py.
    None quando a escola não tem lat/long ou cai fora dos polígonos mapeados."""


def _normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.strip().upper()


def _bairro_base(bairro: str) -> str:
    return bairro.split(" - ", 1)[0].split(" (", 1)[0].strip()


def _resolver_query_a() -> Path:
    gz = QUERY_A_DIR / "01_QueryA_InscricoesPorAno.csv.gz"
    csv = QUERY_A_DIR / "01_QueryA_InscricoesPorAno.csv"
    if gz.exists():
        return gz
    if csv.exists():
        return csv
    raise FileNotFoundError(
        "Não encontrei 01_QueryA_InscricoesPorAno.csv(.gz) em "
        f"{QUERY_A_DIR} — esses dados são fornecidos fora do git (ver "
        "CLAUDE.md), confirme se desafio/ está presente localmente."
    )


def _indice_concorrencia(taxa_atendimento: float | None) -> float | None:
    """Quanto menor a taxa histórica de atendimento, mais concorrida é a escola."""
    if taxa_atendimento is None:
        return None
    return 1.0 - taxa_atendimento


def recalcular_de_desafio() -> list[Escola]:
    """Lê desafio/ do zero e devolve a lista completa de escolas com tag.

    Só usada por scripts/gerar_dataset.py (local, com desafio/ presente) para
    gerar dados/escolas.duckdb — em produção/deploy usa-se carregar_escolas().
    """
    if not ESCOLAS_XLSX.exists():
        raise FileNotFoundError(f"Não encontrei {ESCOLAS_XLSX} — confirme se desafio/ está presente.")

    con = duckdb.connect()
    con.execute("INSTALL excel; LOAD excel;")

    escolas_raw = con.execute(
        f"""
        SELECT
            TRY_CAST(DESIGNACAO AS BIGINT) AS esc_codigo_num,
            DENOMINACAO AS nome,
            RUA AS endereco,
            BAIRRO AS bairro,
            LATITUDE AS latitude,
            LONGITUDE AS longitude,
            Tipo AS tipo
        FROM read_xlsx('{ESCOLAS_XLSX.as_posix()}')
        WHERE DESIGNACAO IS NOT NULL AND BAIRRO IS NOT NULL
        """
    ).fetchall()
    colunas = [d[0] for d in con.description]

    query_a_path = _resolver_query_a()
    situacoes_atendidas = ", ".join(f"'{s}'" for s in ATENDIDA)
    taxa_por_unidade = dict(
        con.execute(
            f"""
            SELECT TRY_CAST(unidade AS BIGINT) AS esc_codigo_num,
                   AVG(CASE WHEN situacao IN ({situacoes_atendidas}) THEN 1.0 ELSE 0.0 END) AS taxa
            FROM read_csv_auto('{query_a_path.as_posix()}', delim=';', header=true,
                                encoding='utf-8', ignore_errors=true)
            GROUP BY 1
            """
        ).fetchall()
    )

    microarea.carregar_microareas(con)
    pontos_escolas = {
        str(registro["esc_codigo_num"]): (registro["latitude"], registro["longitude"])
        for registro in (dict(zip(colunas, linha)) for linha in escolas_raw)
        if registro["latitude"] is not None and registro["longitude"] is not None
    }
    microarea_por_escola = microarea.atribuir_microarea_lote(con, pontos_escolas)
    con.close()

    escolas = []
    for linha in escolas_raw:
        registro = dict(zip(colunas, linha))
        esc_codigo_num = registro["esc_codigo_num"]
        taxa = taxa_por_unidade.get(esc_codigo_num)
        cod_territ, cre = microarea_por_escola.get(str(esc_codigo_num), (None, None))
        escolas.append(
            Escola(
                esc_codigo=str(esc_codigo_num),
                nome=registro["nome"],
                endereco=registro["endereco"],
                bairro=registro["bairro"],
                latitude=registro["latitude"],
                longitude=registro["longitude"],
                tipo=registro["tipo"],
                indice_concorrencia=_indice_concorrencia(taxa),
                cod_territ=cod_territ,
                cre=cre,
            )
        )
    return escolas


def carregar_escolas() -> list[Escola]:
    """Lê dados/escolas.duckdb (pré-processado, commitado no git).

    Rápida e sem dependência de desafio/ nem das extensões excel/spatial em
    runtime — é o que roda em produção/deploy (inclusive Vercel). Se o
    arquivo pré-processado ainda não existir (ex.: acabou de clonar o repo e
    ainda não rodou scripts/gerar_dataset.py), cai para
    recalcular_de_desafio() como conveniência de desenvolvimento local.
    """
    if not DATASET_PRECOMPUTADO.exists():
        return recalcular_de_desafio()

    con = duckdb.connect(str(DATASET_PRECOMPUTADO), read_only=True)
    linhas = con.execute(
        """
        SELECT esc_codigo, nome, endereco, bairro, latitude, longitude, tipo,
               indice_concorrencia, cod_territ, cre
        FROM escolas
        """
    ).fetchall()
    con.close()
    return [
        Escola(
            esc_codigo=esc_codigo,
            nome=nome,
            endereco=endereco,
            bairro=bairro,
            latitude=latitude,
            longitude=longitude,
            tipo=tipo,
            indice_concorrencia=indice_concorrencia,
            cod_territ=cod_territ,
            cre=cre,
        )
        for esc_codigo, nome, endereco, bairro, latitude, longitude, tipo, indice_concorrencia, cod_territ, cre in linhas
    ]


def buscar_por_bairro(escolas: list[Escola], bairro: str) -> list[Escola]:
    alvo = _normalizar(_bairro_base(bairro))
    return [e for e in escolas if _normalizar(_bairro_base(e.bairro)) == alvo]
