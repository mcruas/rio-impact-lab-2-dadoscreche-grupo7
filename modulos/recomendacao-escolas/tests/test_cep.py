"""Testes de app/cep.py e GET /cep/{cep}.

Usa a API real do ViaCEP (sem mock) — precisa de rede. Se estiver offline,
esses testes falham; os demais módulos de teste não dependem de rede.
"""

import pytest
from fastapi.testclient import TestClient

from app.cep import resolver_bairro_por_cep
from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_resolver_bairro_cep_valido() -> None:
    assert resolver_bairro_por_cep("23050-300") == "Campo Grande"


def test_resolver_bairro_aceita_sem_hifen() -> None:
    assert resolver_bairro_por_cep("23050300") == "Campo Grande"


def test_resolver_bairro_cep_invalido_retorna_none() -> None:
    assert resolver_bairro_por_cep("00000-000") is None


def test_resolver_bairro_texto_nao_numerico_retorna_none() -> None:
    assert resolver_bairro_por_cep("abc") is None
    assert resolver_bairro_por_cep("") is None


def test_endpoint_cep_valido(client: TestClient) -> None:
    resp = client.get("/cep/23050-300")
    assert resp.status_code == 200
    assert resp.json() == {"bairro": "Campo Grande"}


def test_endpoint_cep_invalido_retorna_404(client: TestClient) -> None:
    resp = client.get("/cep/00000-000")
    assert resp.status_code == 404
