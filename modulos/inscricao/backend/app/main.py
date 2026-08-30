"""Backend de Inscrição — contrato em contracts/inscricao.openapi.yaml.

Persiste de verdade em Postgres (hospedado no Railway — ver ../README.md),
via DATABASE_URL. Rodar (a partir desta pasta, modulos/inscricao/backend/):
    uvicorn app.main:app --reload
"""

from __future__ import annotations

import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .db import RepositorioInscricoes, get_repositorio
from .models import Inscricao, InscricaoRequest

app = FastAPI(title="Inscrição", version="1.0.0")

_cors_origins = os.environ.get("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_origins == "*" else _cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/inscricoes", response_model=Inscricao, status_code=201)
def criar_inscricao(
    pedido: InscricaoRequest, repositorio: RepositorioInscricoes = Depends(get_repositorio)
) -> Inscricao:
    return repositorio.criar(pedido)


@app.get("/inscricoes/{cpf}", response_model=Inscricao)
def buscar_inscricao(
    cpf: str, repositorio: RepositorioInscricoes = Depends(get_repositorio)
) -> Inscricao:
    inscricao = repositorio.buscar_por_cpf(cpf)
    if inscricao is None:
        raise HTTPException(status_code=404, detail="Nenhuma inscrição encontrada para esse CPF")
    return inscricao
