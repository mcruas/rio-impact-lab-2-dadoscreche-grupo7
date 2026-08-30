from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.db import get_repositorio
from app.main import app
from app.models import Inscricao, InscricaoRequest


class RepositorioFalso:
    """Implementa o mesmo protocolo de app.db.RepositorioInscricoes, em memória."""

    def __init__(self) -> None:
        self._inscricoes: list[Inscricao] = []

    def criar(self, pedido: InscricaoRequest) -> Inscricao:
        inscricao = Inscricao(
            id=str(uuid.uuid4()),
            criado_em=datetime.now(timezone.utc),
            status="Recebida",
            **pedido.model_dump(),
        )
        self._inscricoes.append(inscricao)
        return inscricao

    def buscar_por_cpf(self, cpf: str) -> Inscricao | None:
        for inscricao in self._inscricoes:
            if inscricao.crianca.cpf == cpf or inscricao.responsavel.cpf == cpf:
                return inscricao
        return None


@pytest.fixture
def repositorio() -> RepositorioFalso:
    fake = RepositorioFalso()
    app.dependency_overrides[get_repositorio] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_repositorio, None)


@pytest.fixture
def client(repositorio: RepositorioFalso) -> TestClient:
    return TestClient(app)


PEDIDO_VALIDO = {
    "crianca": {"nome": "Ana Silva", "cpf": "11111111111", "data_nascimento": "2022-01-01"},
    "responsavel": {"cpf": "22222222222"},
    "enderecos_interesse": [{"tipo": "Moradia", "bairro": "Centro"}],
    "turno": "Integral",
    "escolas_escolhidas": ["0724602"],
}


def test_criar_inscricao_retorna_201_com_id_gerado(client: TestClient) -> None:
    resposta = client.post("/inscricoes", json=PEDIDO_VALIDO)
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["id"]
    assert corpo["status"] == "Recebida"
    assert corpo["crianca"]["cpf"] == "11111111111"


def test_busca_por_cpf_da_crianca(client: TestClient) -> None:
    client.post("/inscricoes", json=PEDIDO_VALIDO)
    resposta = client.get("/inscricoes/11111111111")
    assert resposta.status_code == 200
    assert resposta.json()["crianca"]["cpf"] == "11111111111"


def test_busca_por_cpf_do_responsavel(client: TestClient) -> None:
    client.post("/inscricoes", json=PEDIDO_VALIDO)
    resposta = client.get("/inscricoes/22222222222")
    assert resposta.status_code == 200
    assert resposta.json()["responsavel"]["cpf"] == "22222222222"


def test_busca_por_cpf_desconhecido_retorna_404(client: TestClient) -> None:
    resposta = client.get("/inscricoes/99999999999")
    assert resposta.status_code == 404


def test_criar_inscricao_sem_endereco_moradia_retorna_422(client: TestClient) -> None:
    pedido = {**PEDIDO_VALIDO, "enderecos_interesse": [{"tipo": "Trabalho", "bairro": "Centro"}]}
    resposta = client.post("/inscricoes", json=pedido)
    assert resposta.status_code == 422
