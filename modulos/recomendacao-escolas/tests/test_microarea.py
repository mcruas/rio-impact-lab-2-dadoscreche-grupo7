import duckdb
import pytest

from app import microarea


@pytest.fixture(scope="module")
def con() -> duckdb.DuckDBPyConnection:
    conexao = duckdb.connect()
    microarea.carregar_microareas(conexao)
    return conexao


def test_atribuir_microarea_ponto_dentro_do_municipio(con: duckdb.DuckDBPyConnection) -> None:
    resultado = microarea.atribuir_microarea(con, -22.9, -43.2)
    assert resultado is not None
    cod_territ, cre = resultado
    assert cod_territ
    assert isinstance(cre, int)


def test_atribuir_microarea_ponto_fora_do_municipio_retorna_none(con: duckdb.DuckDBPyConnection) -> None:
    # Sao Paulo, bem longe de qualquer poligono do Rio.
    assert microarea.atribuir_microarea(con, -23.5505, -46.6333) is None


def test_atribuir_microarea_lote_bate_com_atribuicao_pontual(con: duckdb.DuckDBPyConnection) -> None:
    pontual = microarea.atribuir_microarea(con, -22.9, -43.2)
    lote = microarea.atribuir_microarea_lote(con, {"ponto_rio": (-22.9, -43.2), "ponto_sp": (-23.5505, -46.6333)})
    assert lote == {"ponto_rio": pontual}


def test_atribuir_microarea_lote_vazio() -> None:
    conexao = duckdb.connect()
    microarea.carregar_microareas(conexao)
    assert microarea.atribuir_microarea_lote(conexao, {}) == {}
