"""Persistência via Postgres (hospedado no Railway) — psycopg puro, sem ORM.

Uma conexão nova por request (padrão recomendado pra funções serverless: o
DATABASE_URL aponta pra um endpoint com proxy TCP público, então não há
ganho em manter um pool próprio vivo entre invocações que podem cair em
instâncias diferentes a qualquer momento).
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import Protocol

import psycopg
from psycopg.rows import dict_row

from .models import Inscricao, InscricaoRequest

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS inscricoes (
    id TEXT PRIMARY KEY,
    cpf_crianca TEXT NOT NULL,
    cpf_responsavel TEXT NOT NULL,
    turno TEXT NOT NULL,
    status TEXT NOT NULL,
    criado_em TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_inscricoes_cpf_crianca ON inscricoes (cpf_crianca);
CREATE INDEX IF NOT EXISTS idx_inscricoes_cpf_responsavel ON inscricoes (cpf_responsavel);
"""


def _connection_url() -> str:
    url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL (ou POSTGRES_URL) não configurada — crie um Postgres "
            "(ex.: Railway, ver ../../ARQUITETURA.md) e exporte a connection "
            "string, ou copie .env.example para .env.local."
        )
    return url


class RepositorioInscricoes(Protocol):
    def criar(self, pedido: InscricaoRequest) -> Inscricao: ...
    def buscar_por_cpf(self, cpf: str) -> Inscricao | None: ...


class PostgresRepositorioInscricoes:
    def __init__(self) -> None:
        self._schema_pronto = False

    def _conectar(self) -> psycopg.Connection:
        conn = psycopg.connect(_connection_url(), row_factory=dict_row)
        if not self._schema_pronto:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA_SQL)
            conn.commit()
            self._schema_pronto = True
        return conn

    def criar(self, pedido: InscricaoRequest) -> Inscricao:
        inscricao = Inscricao(
            id=str(uuid.uuid4()),
            criado_em=datetime.now(timezone.utc),
            status="Recebida",
            **pedido.model_dump(),
        )
        payload = inscricao.model_dump(mode="json")
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inscricoes
                    (id, cpf_crianca, cpf_responsavel, turno, status, criado_em, payload)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    inscricao.id,
                    inscricao.crianca.cpf,
                    inscricao.responsavel.cpf,
                    inscricao.turno,
                    inscricao.status,
                    inscricao.criado_em,
                    json.dumps(payload),
                ),
            )
            conn.commit()
        return inscricao

    def buscar_por_cpf(self, cpf: str) -> Inscricao | None:
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT payload FROM inscricoes
                WHERE cpf_crianca = %s OR cpf_responsavel = %s
                ORDER BY criado_em DESC
                LIMIT 1
                """,
                (cpf, cpf),
            )
            linha = cur.fetchone()
        if linha is None:
            return None
        return Inscricao.model_validate(linha["payload"])


_repositorio: RepositorioInscricoes | None = None


def get_repositorio() -> RepositorioInscricoes:
    global _repositorio
    if _repositorio is None:
        _repositorio = PostgresRepositorioInscricoes()
    return _repositorio
