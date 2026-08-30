"""Modelos Pydantic — devem espelhar contracts/schemas/*.schema.json."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

TIPO_MORADIA = "Moradia"
"""Único tipo obrigatório em enderecos_interesse — os demais são livres
(Trabalho, ou qualquer outro local de desejo da família: avós, escola atual etc.)."""


class Crianca(BaseModel):
    """Espelha contracts/schemas/crianca.schema.json."""

    nome: str = Field(min_length=1)
    cpf: str = Field(pattern=r"^[0-9]{11}$")
    data_nascimento: date


class Responsavel(BaseModel):
    """Espelha contracts/schemas/responsavel.schema.json."""

    cpf: str = Field(pattern=r"^[0-9]{11}$")


class Endereco(BaseModel):
    """Espelha contracts/schemas/endereco.schema.json."""

    tipo: str = Field(min_length=1)
    logradouro: str | None = None
    numero: str | None = None
    complemento: str | None = None
    bairro: str = Field(min_length=1)
    cep: str | None = Field(default=None, pattern=r"^[0-9]{8}$")


class InscricaoRequest(BaseModel):
    """Corpo de POST /inscricoes — espelha inscricao.schema.json, exceto os
    campos gerados pelo servidor (id, status, criado_em)."""

    crianca: Crianca
    responsavel: Responsavel
    enderecos_interesse: list[Endereco] = Field(min_length=1, max_length=5)
    turno: str = Field(pattern=r"^(Integral|Parcial)$")
    escolas_escolhidas: list[str] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def _validar_pelo_menos_moradia(self) -> "InscricaoRequest":
        if not any(e.tipo == TIPO_MORADIA for e in self.enderecos_interesse):
            raise ValueError(f"é necessário informar ao menos um endereço com tipo={TIPO_MORADIA!r}")
        return self


class Inscricao(InscricaoRequest):
    """Espelha inscricao.schema.json por completo (inclui os campos gerados)."""

    id: str
    status: str = "Recebida"
    criado_em: datetime
