"""Testes do backend de Recomendação de Escola.

Usa os dados reais de desafio/ (sem mocks) — por isso o primeiro teste que
toca a fixture `client` é mais lento (carrega e junta os arquivos uma vez,
resultado é cacheado em memória para os demais testes do módulo).
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_bairro_conhecido_retorna_escolas(client: TestClient) -> None:
    resp = client.get("/escolas", params={"bairro": "Tijuca"})
    assert resp.status_code == 200
    escolas = resp.json()
    assert len(escolas) > 0
    for escola in escolas:
        assert escola["tag_priorizacao"] in ("Alta", "Média", "Baixa", "Sem dado")
        assert escola["esc_codigo"]


def test_bairro_sem_acento_encontra_mesmas_escolas(client: TestClient) -> None:
    com_acento = client.get("/escolas", params={"bairro": "Tijuca"}).json()
    sem_acento_variacao_caixa = client.get("/escolas", params={"bairro": "TIJUCA"}).json()
    assert {e["esc_codigo"] for e in com_acento} == {e["esc_codigo"] for e in sem_acento_variacao_caixa}


def test_bairro_inexistente_retorna_lista_vazia(client: TestClient) -> None:
    resp = client.get("/escolas", params={"bairro": "Bairro Que Nao Existe De Verdade"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_bairro_vazio_retorna_422(client: TestClient) -> None:
    resp = client.get("/escolas", params={"bairro": "   "})
    assert resp.status_code == 422


def test_bairro_ausente_retorna_422(client: TestClient) -> None:
    resp = client.get("/escolas")
    assert resp.status_code == 422
