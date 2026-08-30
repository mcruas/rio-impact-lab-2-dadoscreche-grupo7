"""Motor de pontuação/explicabilidade das recomendações.

Três sinais, cada um 0-100 (exceto histórico, que só penaliza), combinados por uma
soma ponderada — deliberadamente simples e transparente (nada de modelo caixa-preta),
porque o requisito central é conseguir explicar cada sugestão na página de admin
(ver app/main.py, rota /admin/recomendacoes).

Pesos (proximidade dominante, por pedido explícito do time):
    pontuacao_final = 0.5*proximidade + 0.3*adequacao_score + 0.2*historico

Ajustar os pesos abaixo se o comportamento observado não fizer sentido na prática —
eles são só constantes nomeadas, não há nada "aprendido" nelas.
"""

from __future__ import annotations

from dataclasses import dataclass

PESO_PROXIMIDADE = 0.5
PESO_ADEQUACAO_SCORE = 0.3
PESO_HISTORICO = 0.2

RAIO_MAX_KM = 10.0
NEUTRO_ADEQUACAO_SCORE = 50.0
PENALIDADE_HISTORICO_MAXIMA = 50.0


@dataclass(frozen=True)
class Rationale:
    pontos_proximidade: float
    pontos_adequacao_score: float
    pontos_historico: float
    explicacao: str

    @property
    def pontuacao_final(self) -> float:
        return (
            PESO_PROXIMIDADE * self.pontos_proximidade
            + PESO_ADEQUACAO_SCORE * self.pontos_adequacao_score
            + PESO_HISTORICO * self.pontos_historico
        )


def pontos_proximidade(distancia_km: float | None, raio_max_km: float = RAIO_MAX_KM) -> float:
    """100 se a distância é ~0, decai linearmente até 0 no raio_max_km."""
    if distancia_km is None:
        return 0.0
    return max(0.0, 100.0 * (1 - distancia_km / raio_max_km))


def pontos_adequacao_score(percentil_score: float | None, indice_concorrencia: float | None) -> float:
    """Casa o percentil do score da família com o quão concorrida é a escola.

    Score alto (percentil perto de 1) + escola muito concorrida (índice perto de 1)
    => pontuação alta (é um "risco" adequado ao perfil). Score baixo + escola muito
    concorrida => pontuação baixa (dificilmente vai conseguir). Sem informação de um
    dos dois lados, devolve um valor neutro (nem incentiva nem desincentiva).
    """
    if percentil_score is None or indice_concorrencia is None:
        return NEUTRO_ADEQUACAO_SCORE
    return 100.0 * (1 - abs(percentil_score - indice_concorrencia))


def pontos_historico(
    vezes_convocado: int | None,
    vezes_nao_compareceu: int | None,
    indice_concorrencia: float | None,
) -> float:
    """Penaliza escolas concorridas para responsáveis com histórico de não-comparecimento.

    Só penaliza proporcional à taxa observada de não-comparecimento E ao quão
    concorrida é a escola — sem histórico (ninguém foi convocado ainda) ou em
    escola pouco concorrida, a penalidade é zero.
    """
    if not vezes_convocado or indice_concorrencia is None:
        return 0.0
    taxa_nao_comparecimento = (vezes_nao_compareceu or 0) / vezes_convocado
    return -PENALIDADE_HISTORICO_MAXIMA * taxa_nao_comparecimento * indice_concorrencia


def _explicar(
    distancia_km: float | None,
    origem_distancia: str | None,
    indice_concorrencia: float | None,
    percentil_score: float | None,
    pts_historico: float,
) -> str:
    partes = []
    if distancia_km is not None:
        preposicao = {"Moradia": "da moradia", "Trabalho": "do trabalho"}.get(
            origem_distancia, str(origem_distancia).lower()
        )
        partes.append(f"a {distancia_km:.1f} km {preposicao}")
    else:
        partes.append("sem distância calculável (bairro não reconhecido ou escola sem coordenadas)")

    if indice_concorrencia is None:
        partes.append("sem histórico de concorrência nesta unidade")
    elif indice_concorrencia >= 0.6:
        partes.append("historicamente muito concorrida")
    elif indice_concorrencia >= 0.3:
        partes.append("concorrência histórica moderada")
    else:
        partes.append("historicamente pouco concorrida")

    if percentil_score is not None and indice_concorrencia is not None:
        partes.append(f"compatível com o percentil de score informado ({percentil_score:.0%})")

    if pts_historico < 0:
        partes.append("penalizada por histórico de não-comparecimento do responsável em vagas concorridas")

    return "; ".join(partes).capitalize() + "."


def montar_rationale(
    *,
    distancia_km: float | None,
    origem_distancia: str | None,
    indice_concorrencia: float | None,
    percentil_score: float | None,
    vezes_convocado: int | None,
    vezes_nao_compareceu: int | None,
) -> Rationale:
    pts_prox = pontos_proximidade(distancia_km)
    pts_adeq = pontos_adequacao_score(percentil_score, indice_concorrencia)
    pts_hist = pontos_historico(vezes_convocado, vezes_nao_compareceu, indice_concorrencia)
    explicacao = _explicar(distancia_km, origem_distancia, indice_concorrencia, percentil_score, pts_hist)
    return Rationale(
        pontos_proximidade=pts_prox,
        pontos_adequacao_score=pts_adeq,
        pontos_historico=pts_hist,
        explicacao=explicacao,
    )
