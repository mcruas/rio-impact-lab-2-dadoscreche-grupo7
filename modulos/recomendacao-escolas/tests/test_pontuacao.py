from app.pontuacao import (
    NEUTRO_ADEQUACAO_SCORE,
    montar_rationale,
    pontos_adequacao_score,
    pontos_historico,
    pontos_proximidade,
)


def test_pontos_proximidade_maximo_quando_distancia_zero() -> None:
    assert pontos_proximidade(0.0) == 100.0


def test_pontos_proximidade_zero_no_raio_maximo() -> None:
    assert pontos_proximidade(10.0, raio_max_km=10.0) == 0.0


def test_pontos_proximidade_nao_fica_negativo_alem_do_raio() -> None:
    assert pontos_proximidade(50.0, raio_max_km=10.0) == 0.0


def test_pontos_proximidade_none_vira_zero() -> None:
    assert pontos_proximidade(None) == 0.0


def test_pontos_adequacao_score_neutro_sem_informacao() -> None:
    assert pontos_adequacao_score(None, 0.8) == NEUTRO_ADEQUACAO_SCORE
    assert pontos_adequacao_score(0.8, None) == NEUTRO_ADEQUACAO_SCORE


def test_pontos_adequacao_score_maximo_quando_score_bate_com_concorrencia() -> None:
    assert pontos_adequacao_score(0.9, 0.9) == 100.0
    assert pontos_adequacao_score(0.1, 0.1) == 100.0


def test_pontos_adequacao_score_penaliza_descompasso() -> None:
    # score baixo pedindo escola de altíssima concorrência: pontuação baixa
    baixo = pontos_adequacao_score(0.1, 0.95)
    alto = pontos_adequacao_score(0.9, 0.95)
    assert baixo < alto


def test_pontos_historico_zero_sem_convocacoes() -> None:
    assert pontos_historico(0, 0, 0.9) == 0.0
    assert pontos_historico(None, None, 0.9) == 0.0


def test_pontos_historico_zero_em_escola_pouco_concorrida() -> None:
    assert pontos_historico(10, 10, 0.0) == 0.0


def test_pontos_historico_penaliza_mais_quanto_mais_concorrida() -> None:
    penalidade_baixa_concorrencia = pontos_historico(10, 10, 0.2)
    penalidade_alta_concorrencia = pontos_historico(10, 10, 0.9)
    assert penalidade_alta_concorrencia < penalidade_baixa_concorrencia < 0


def test_montar_rationale_pontuacao_final_combina_os_tres_pesos() -> None:
    rationale = montar_rationale(
        distancia_km=0.0,
        origem_distancia="Moradia",
        indice_concorrencia=0.8,
        percentil_score=0.8,
        vezes_convocado=0,
        vezes_nao_compareceu=0,
    )
    # proximidade=100, adequacao=100, historico=0 -> 0.5*100 + 0.3*100 + 0.2*0 = 80
    assert rationale.pontuacao_final == 80.0
    assert "moradia" in rationale.explicacao.lower()
