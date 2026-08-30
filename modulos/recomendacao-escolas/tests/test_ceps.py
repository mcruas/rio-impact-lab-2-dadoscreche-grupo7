"""Testes de app/ceps.py e dos CSVs commitados em dados/.

Rodam contra os arquivos versionados, sem precisar de desafio/ nem de rede — a mesma
garantia que vale em produção. Se algum falhar depois de regerar os dados, é sinal de
que scripts/gerar_ceps.py mudou de comportamento, não de que o teste está velho.
"""

from __future__ import annotations

import re

import pytest

from app.ceps import (
    ORIGENS_COORD,
    VIZINHAS_POR_CEP,
    carregar_cep_escolas,
    carregar_ceps,
    normalizar_cep,
)
from app.data import carregar_escolas

# Caixa envolvente do município do Rio, folgada. Serve para pegar erro grosseiro de
# projeção — em especial o ST_Transform sem always_xy, que joga o ponto para longe.
LAT_MIN, LAT_MAX = -23.15, -22.70
LON_MIN, LON_MAX = -43.85, -43.05


@pytest.fixture(scope="module")
def ceps():
    return carregar_ceps()


@pytest.fixture(scope="module")
def cep_escolas():
    return carregar_cep_escolas()


def test_normalizar_cep_aceita_com_e_sem_hifen() -> None:
    assert normalizar_cep("23050-300") == "23050300"
    assert normalizar_cep("23050300") == "23050300"


def test_normalizar_cep_rejeita_tamanho_errado_e_vazio() -> None:
    assert normalizar_cep("2305030") is None
    assert normalizar_cep("230503000") is None
    assert normalizar_cep("abc") is None
    assert normalizar_cep("") is None
    assert normalizar_cep(None) is None


def test_dataset_de_ceps_foi_gerado(ceps) -> None:
    assert len(ceps) > 20000


def test_cep_e_chave_valida_de_8_digitos(ceps) -> None:
    # Mesmo formato exigido por contracts/schemas/endereco.schema.json.
    assert all(re.fullmatch(r"[0-9]{8}", cep) for cep in ceps)
    assert all(cep == registro.cep for cep, registro in ceps.items())


def test_coordenadas_caem_dentro_do_rio(ceps) -> None:
    fora = [
        r for r in ceps.values()
        if not (LAT_MIN <= r.latitude <= LAT_MAX and LON_MIN <= r.longitude <= LON_MAX)
    ]
    assert fora == []


def test_origem_coord_so_tem_valores_previstos(ceps) -> None:
    assert {r.origem_coord for r in ceps.values()} <= set(ORIGENS_COORD)


def test_cascata_resolve_quase_toda_a_demanda_com_precisao_de_cep(ceps) -> None:
    """As origens boas (CEP exato / prefixo de 5) devem cobrir >=95% das inscrições.

    Ponderado por n_inscricoes, não por CEP distinto: errar um CEP de alta demanda é
    muito pior que errar um CEP com uma inscrição só.
    """
    total = sum(r.n_inscricoes for r in ceps.values())
    precisos = sum(
        r.n_inscricoes for r in ceps.values() if r.origem_coord in ("cep_exato", "prefixo5")
    )
    assert precisos / total >= 0.95


def test_maioria_dos_ceps_tem_microarea(ceps) -> None:
    com_microarea = sum(1 for r in ceps.values() if r.cod_territ is not None)
    assert com_microarea / len(ceps) >= 0.99


def test_cre_e_coerente_com_cod_territ(ceps) -> None:
    # cod_territ '4.16' pertence à CRE 4 — o prefixo antes do ponto é a CRE.
    for r in ceps.values():
        if r.cod_territ is None:
            continue
        assert r.cre == int(r.cod_territ.split(".")[0])


def test_vizinhanca_cobre_os_mesmos_ceps(ceps, cep_escolas) -> None:
    assert set(cep_escolas) == set(ceps)


def test_vizinhanca_tem_ordem_contigua_a_partir_de_1(cep_escolas) -> None:
    for vizinhas in cep_escolas.values():
        assert [v.ordem for v in vizinhas] == list(range(1, len(vizinhas) + 1))
        assert len(vizinhas) == VIZINHAS_POR_CEP


def test_vizinhanca_esta_ordenada_por_distancia(cep_escolas) -> None:
    for vizinhas in cep_escolas.values():
        distancias = [v.distancia_km for v in vizinhas]
        assert distancias == sorted(distancias)
        assert all(d >= 0 for d in distancias)


def test_escolas_da_vizinhanca_existem_no_catalogo(cep_escolas) -> None:
    """Pega o erro de zero à esquerda: escolas.duckdb guarda '123701' e a Query A
    usa '0123701'. Se o gerador gravar no formato errado, nada aqui casa."""
    catalogo = {e.esc_codigo for e in carregar_escolas()}
    usados = {v.esc_codigo for vizinhas in cep_escolas.values() for v in vizinhas}
    assert usados <= catalogo
