"""Backend de Recomendação de Escola — contrato em contracts/recomendacao-escolas.openapi.yaml.

Rodar (a partir desta pasta, modulos/recomendacao-escolas/):
    uvicorn app.main:app --reload

Não depende de nenhum outro módulo — só dos dados em desafio/.
"""

from fastapi import FastAPI, HTTPException, Query

from .data import Escola, buscar_por_bairro, carregar_escolas
from .models import EscolaResponse

app = FastAPI(title="Recomendação de Escola", version="1.0.0")

_escolas_cache: list[Escola] | None = None


def _escolas() -> list[Escola]:
    global _escolas_cache
    if _escolas_cache is None:
        _escolas_cache = carregar_escolas()
    return _escolas_cache


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/escolas", response_model=list[EscolaResponse])
def escolas(bairro: str = Query(..., min_length=1)) -> list[EscolaResponse]:
    bairro = bairro.strip()
    if not bairro:
        raise HTTPException(status_code=422, detail="bairro não pode ser vazio")
    encontradas = buscar_por_bairro(_escolas(), bairro)
    return [EscolaResponse(**e.__dict__) for e in encontradas]
