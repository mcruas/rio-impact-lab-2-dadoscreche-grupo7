"""Modelos Pydantic — devem espelhar contracts/schemas/escola.schema.json."""

from enum import Enum

from pydantic import BaseModel


class TagPriorizacao(str, Enum):
    ALTA = "Alta"
    MEDIA = "Média"
    BAIXA = "Baixa"
    SEM_DADO = "Sem dado"


class EscolaResponse(BaseModel):
    esc_codigo: str
    nome: str
    endereco: str | None = None
    bairro: str
    latitude: float | None = None
    longitude: float | None = None
    tipo: str | None = None
    tag_priorizacao: TagPriorizacao
    taxa_atendimento_historica: float | None = None
