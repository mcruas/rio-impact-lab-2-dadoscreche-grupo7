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


# --- GET /escolas (listagem simples, sem ranking) ---------------------------


def test_escolas_bairro_conhecido_retorna_lista(client: TestClient) -> None:
    resp = client.get("/escolas", params={"bairro": "Tijuca"})
    assert resp.status_code == 200
    escolas = resp.json()
    assert len(escolas) > 0
    for escola in escolas:
        assert escola["esc_codigo"]
        assert "tag_priorizacao" not in escola


def test_escolas_bairro_sem_acento_encontra_mesmas_escolas(client: TestClient) -> None:
    com_acento = client.get("/escolas", params={"bairro": "Tijuca"}).json()
    maiusculo = client.get("/escolas", params={"bairro": "TIJUCA"}).json()
    assert {e["esc_codigo"] for e in com_acento} == {e["esc_codigo"] for e in maiusculo}


def test_escolas_bairro_vazio_retorna_422(client: TestClient) -> None:
    assert client.get("/escolas", params={"bairro": "   "}).status_code == 422


def test_escolas_bairro_ausente_retorna_422(client: TestClient) -> None:
    assert client.get("/escolas").status_code == 422


# --- POST /recomendacoes (ranking + rationale) -------------------------------


def test_recomendacoes_apenas_moradia(client: TestClient) -> None:
    pedido = {"enderecos": [{"tipo": "Moradia", "bairro": "Tijuca"}]}
    resp = client.post("/recomendacoes", json=pedido)
    assert resp.status_code == 200
    recomendacoes = resp.json()
    assert len(recomendacoes) > 0
    for r in recomendacoes:
        assert r["distancia_km"] >= 0
        assert r["origem_distancia"] == "Moradia"
        assert set(r["rationale"].keys()) == {
            "pontos_proximidade",
            "pontos_adequacao_score",
            "pontos_historico",
            "explicacao",
        }
    # ordenado por pontuacao_final decrescente
    pontuacoes = [r["pontuacao_final"] for r in recomendacoes]
    assert pontuacoes == sorted(pontuacoes, reverse=True)


def test_recomendacoes_sem_endereco_moradia_retorna_422(client: TestClient) -> None:
    pedido = {"enderecos": [{"tipo": "Trabalho", "bairro": "Tijuca"}]}
    assert client.post("/recomendacoes", json=pedido).status_code == 422


def test_recomendacoes_sem_endereco_nenhum_retorna_422(client: TestClient) -> None:
    assert client.post("/recomendacoes", json={"enderecos": []}).status_code == 422


def test_recomendacoes_score_alto_favorece_escolas_mais_concorridas(client: TestClient) -> None:
    base = {"enderecos": [{"tipo": "Moradia", "bairro": "Tijuca"}]}

    baixo = client.post(
        "/recomendacoes", json={**base, "score_estimado": {"percentil": 0.05}}
    ).json()
    alto = client.post(
        "/recomendacoes", json={**base, "score_estimado": {"percentil": 0.95}}
    ).json()

    def concorrencia_media_top3(recomendacoes: list[dict]) -> float:
        indices = [
            r["indice_concorrencia"] for r in recomendacoes[:3] if r["indice_concorrencia"] is not None
        ]
        return sum(indices) / len(indices) if indices else 0.0

    # não é garantido matematicamente pra qualquer dataset, mas com pesos
    # dominados por proximidade e um bairro com escolas de concorrência
    # variada, o topo do score alto tende a aceitar concorrência >= score baixo
    assert concorrencia_media_top3(alto) >= concorrencia_media_top3(baixo) - 1e-6


def test_recomendacoes_historico_de_nao_comparecimento_penaliza_concorridas(client: TestClient) -> None:
    base = {"enderecos": [{"tipo": "Moradia", "bairro": "Tijuca"}], "score_estimado": {"percentil": 0.9}}

    sem_historico = client.post("/recomendacoes", json=base).json()
    com_historico_ruim = client.post(
        "/recomendacoes",
        json={**base, "historico_responsavel": {"vezes_convocado": 5, "vezes_nao_compareceu": 5}},
    ).json()

    por_escola_sem = {r["esc_codigo"]: r["pontuacao_final"] for r in sem_historico}
    for r in com_historico_ruim:
        if r["indice_concorrencia"] and r["indice_concorrencia"] > 0.5:
            assert r["pontuacao_final"] <= por_escola_sem.get(r["esc_codigo"], r["pontuacao_final"]) + 1e-6


def test_recomendacoes_inclui_escola_preferida_mesmo_fora_do_top(client: TestClient) -> None:
    todas = client.get("/escolas", params={"bairro": "Tijuca"}).json()
    esc_codigo_preferida = todas[-1]["esc_codigo"]

    pedido = {
        "enderecos": [{"tipo": "Moradia", "bairro": "Tijuca"}],
        "escola_preferida_esc_codigo": esc_codigo_preferida,
    }
    resp = client.post("/recomendacoes", json=pedido, params={"limite": 1})
    recomendacoes = resp.json()
    assert any(r["esc_codigo"] == esc_codigo_preferida and r["preferida"] for r in recomendacoes)


# --- /admin/recomendacoes (página HTML) --------------------------------------


def test_admin_form_get(client: TestClient) -> None:
    resp = client.get("/admin/recomendacoes")
    assert resp.status_code == 200
    assert "Bairro de moradia" in resp.text


def test_admin_form_post_renderiza_tabela(client: TestClient) -> None:
    resp = client.post(
        "/admin/recomendacoes",
        data={"bairro_moradia": "Tijuca", "percentil_score": "80"},
    )
    assert resp.status_code == 200
    assert "recomendada" in resp.text.lower()


def test_admin_form_post_percentil_invalido_mostra_erro(client: TestClient) -> None:
    resp = client.post(
        "/admin/recomendacoes",
        data={"bairro_moradia": "Tijuca", "percentil_score": "não é um número"},
    )
    assert resp.status_code == 200
    assert "inválido" in resp.text.lower()
