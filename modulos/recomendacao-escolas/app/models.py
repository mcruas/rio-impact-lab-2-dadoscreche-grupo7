"""Modelos Pydantic — devem espelhar contracts/schemas/*.schema.json."""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

TIPO_MORADIA = "Moradia"
"""Único tipo obrigatório em PedidoRecomendacao.enderecos — os demais são livres
(Trabalho, ou qualquer outro local de desejo da família: avós, escola atual etc.)."""


class EscolaResponse(BaseModel):
    """Espelha contracts/schemas/escola.schema.json (catálogo, sem ranking)."""

    esc_codigo: str
    nome: str
    endereco: str | None = None
    bairro: str
    latitude: float | None = None
    longitude: float | None = None
    tipo: str | None = None
    cod_territ: str | None = None
    cre: int | None = None


class LocalizacaoCepResponse(BaseModel):
    """Resposta de GET /cep/{cep}.

    `latitude`/`longitude` são adição posterior ao `bairro`, para o frontend poder
    plotar a família no mapa. Ficam nulas quando o CEP só existe no ViaCEP, que não
    devolve coordenada — quem consome tem de aguentar o nulo.
    """

    bairro: str
    latitude: float | None = None
    longitude: float | None = None


class EnderecoRequest(BaseModel):
    """Espelha contracts/schemas/endereco.schema.json."""

    tipo: str = Field(min_length=1)
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str = Field(min_length=1)
    cep: str | None = None


class ScoreEstimadoRequest(BaseModel):
    """Espelha contracts/schemas/score_estimado.schema.json."""

    percentil: float = Field(ge=0, le=1)
    valor: float | None = None


class HistoricoResponsavelRequest(BaseModel):
    """Espelha contracts/schemas/historico_responsavel.schema.json."""

    vezes_convocado: int = Field(ge=0)
    vezes_nao_compareceu: int = Field(ge=0)


class PedidoRecomendacao(BaseModel):
    """Espelha contracts/schemas/pedido_recomendacao.schema.json."""

    enderecos: list[EnderecoRequest] = Field(min_length=1, max_length=5)
    escola_preferida_esc_codigo: str | None = None
    score_estimado: ScoreEstimadoRequest | None = None
    historico_responsavel: HistoricoResponsavelRequest | None = None

    @model_validator(mode="after")
    def _validar_pelo_menos_moradia(self) -> "PedidoRecomendacao":
        if not any(e.tipo == TIPO_MORADIA for e in self.enderecos):
            raise ValueError(f"é necessário informar ao menos um endereço com tipo={TIPO_MORADIA!r}")
        return self


class RationaleResponse(BaseModel):
    pontos_proximidade: float
    pontos_adequacao_score: float
    pontos_historico: float
    explicacao: str


class RecomendacaoEscolaResponse(BaseModel):
    """Espelha contracts/schemas/recomendacao_escola.schema.json."""

    esc_codigo: str
    nome: str
    endereco: str | None = None
    bairro: str
    latitude: float | None = None
    longitude: float | None = None
    tipo: str | None = None
    cod_territ: str | None = None
    cre: int | None = None
    distancia_km: float
    origem_distancia: str
    indice_concorrencia: float | None = None
    preferida: bool = False
    pontuacao_final: float
    rationale: RationaleResponse
