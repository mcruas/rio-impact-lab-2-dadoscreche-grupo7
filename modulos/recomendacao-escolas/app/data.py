"""Carrega e prepara os dados de escolas usados pelo endpoint /escolas.

Fontes (lidas direto de desafio/, sem depender de nenhum outro módulo):
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

REPO_ROOT = Path(__file__).resolve().parents[3]
ESCOLAS_XLSX = (
    REPO_ROOT / "desafio" / "OferecimentosEvagas" / "Unidades_Unificadas_com_Localizacao.xlsx"
)
QUERY_A_DIR = REPO_ROOT / "desafio" / "Bases IC_ ClassificadoseFila"

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
    tag_priorizacao: str
    taxa_atendimento_historica: float | None


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


def _tag_para_taxa(taxa: float | None) -> str:
    if taxa is None:
        return "Sem dado"
    if taxa >= 0.6:
        return "Alta"
    if taxa >= 0.3:
        return "Média"
    return "Baixa"


def carregar_escolas() -> list[Escola]:
    """Lê desafio/ uma vez e devolve a lista completa de escolas com tag."""
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
    con.close()

    escolas = []
    for linha in escolas_raw:
        registro = dict(zip(colunas, linha))
        esc_codigo_num = registro["esc_codigo_num"]
        taxa = taxa_por_unidade.get(esc_codigo_num)
        escolas.append(
            Escola(
                esc_codigo=str(esc_codigo_num),
                nome=registro["nome"],
                endereco=registro["endereco"],
                bairro=registro["bairro"],
                latitude=registro["latitude"],
                longitude=registro["longitude"],
                tipo=registro["tipo"],
                tag_priorizacao=_tag_para_taxa(taxa),
                taxa_atendimento_historica=taxa,
            )
        )
    return escolas


def buscar_por_bairro(escolas: list[Escola], bairro: str) -> list[Escola]:
    alvo = _normalizar(_bairro_base(bairro))
    return [e for e in escolas if _normalizar(_bairro_base(e.bairro)) == alvo]
