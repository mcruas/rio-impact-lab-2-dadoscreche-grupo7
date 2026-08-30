"""Testes de app/cep.py e GET /cep/{cep}.

O caminho normal resolve pela tabela local dados/ceps.csv e **não precisa de rede** —
é o que estes testes cobrem. O fallback para o ViaCEP só vale para CEP fora da tabela;
o teste que realmente sai para a internet está marcado com `@pytest.mark.rede` e pode
ser pulado com `pytest -m "not rede"`.
"""

import pytest
from fastapi.testclient import TestClient

from app.cep import resolver_bairro_por_cep, resolver_cep
from app.ceps import tabela_ceps
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_resolver_bairro_cep_valido() -> None:
    assert resolver_bairro_por_cep("23050-300") == "Campo Grande"


def test_resolver_bairro_aceita_sem_hifen() -> None:
    assert resolver_bairro_por_cep("23050300") == "Campo Grande"


def test_resolver_bairro_texto_nao_numerico_retorna_none() -> None:
    assert resolver_bairro_por_cep("abc") is None
    assert resolver_bairro_por_cep("") is None


def test_resolver_bairro_usa_tabela_local_sem_rede(monkeypatch: pytest.MonkeyPatch) -> None:
    """Derruba o fallback de rede e confirma que os CEPs conhecidos seguem resolvendo."""

    def _explodir(digitos: str) -> str | None:
        raise AssertionError(f"não deveria consultar o ViaCEP para {digitos}")

    monkeypatch.setattr("app.cep._consultar_viacep", _explodir)
    for cep, registro in list(tabela_ceps().items())[:200]:
        assert resolver_bairro_por_cep(cep) == registro.bairro


def test_endpoint_cep_valido(client: TestClient) -> None:
    resp = client.get("/cep/23050-300")
    assert resp.status_code == 200
    corpo = resp.json()
    assert corpo["bairro"] == "Campo Grande"
    # A coordenada é o que permite plotar a família no mapa do frontend.
    assert -23.15 <= corpo["latitude"] <= -22.70
    assert -43.85 <= corpo["longitude"] <= -43.05


def test_endpoint_cep_malformado_retorna_404(client: TestClient) -> None:
    resp = client.get("/cep/abc")
    assert resp.status_code == 404


@pytest.mark.rede
def test_fallback_viacep_para_cep_fora_da_tabela() -> None:
    """CEP de São Paulo: não está na tabela (que é do Rio), então cai no ViaCEP."""
    cep_sp = "01310100"  # Av. Paulista
    assert cep_sp not in tabela_ceps()
    assert resolver_bairro_por_cep(cep_sp) == "Bela Vista"


@pytest.mark.rede
def test_fallback_viacep_cep_inexistente_retorna_none() -> None:
    assert "00000001" not in tabela_ceps()
    assert resolver_bairro_por_cep("00000001") is None


def test_resolver_cep_traz_coordenada_da_tabela_local() -> None:
    localizacao = resolver_cep("23050-300")
    assert localizacao is not None
    assert localizacao.bairro == "Campo Grande"
    assert localizacao.latitude is not None and localizacao.longitude is not None


@pytest.mark.rede
def test_fallback_viacep_nao_tem_coordenada() -> None:
    """O ViaCEP não devolve lat/long — o contrato promete nulo nesse caso."""
    localizacao = resolver_cep("01310100")
    assert localizacao is not None
    assert localizacao.bairro == "Bela Vista"
    assert localizacao.latitude is None and localizacao.longitude is None
