"""Agregador de deploy: monta os 4 backends de módulo num único processo
(um serviço Railway), cada um no seu prefixo de path. Existe só pra
simplificar a topologia de deploy do demo -- não muda nenhum código dos
módulos, e eles continuam se chamando só por HTTP/contrato entre si, nunca
por import direto (ver INTEGRACAO_RMI_WHATSAPP.md e os *.openapi.yaml).

Rodar (a partir da raiz do repo):
    uvicorn deploy.main:app --reload
"""

from __future__ import annotations

import importlib
import sys
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

RAIZ = Path(__file__).resolve().parents[1]
MODULOS = RAIZ / "modulos"


def _montar_pacote(caminho_pacote: Path) -> FastAPI:
    """Importa um backend organizado como pacote `app/` (inscricao,
    recomendacao-escolas). Os dois usam o mesmo nome de pacote top-level
    ("app"), então purga esse nome do cache de sys.modules antes e depois de
    cada import pra um não pisar no outro."""

    def _purgar() -> None:
        for nome in [n for n in sys.modules if n == "app" or n.startswith("app.")]:
            del sys.modules[nome]

    _purgar()
    sys.path.insert(0, str(caminho_pacote))
    try:
        instancia = importlib.import_module("app.main").app
    finally:
        sys.path.remove(str(caminho_pacote))
        _purgar()
    return instancia


def _montar_script(caminho_dir: Path, nomes_do_modulo: list[str]) -> FastAPI:
    """Importa um backend em script solto, sem pacote (acompanhamento,
    match-engine) -- os dois têm um main.py cada, então isola pelo nome de
    todos os módulos top-level que ele e seus vizinhos definem."""

    def _purgar() -> None:
        for nome in nomes_do_modulo:
            sys.modules.pop(nome, None)

    _purgar()
    sys.path.insert(0, str(caminho_dir))
    try:
        instancia = importlib.import_module("main").app
    finally:
        sys.path.remove(str(caminho_dir))
        _purgar()
    return instancia


app_inscricao = _montar_pacote(MODULOS / "inscricao/backend")
app_recomendacao_escolas = _montar_pacote(MODULOS / "recomendacao-escolas")
app_match_engine = _montar_script(MODULOS / "match-engine/backend", ["main", "motor"])
app_acompanhamento = _montar_script(MODULOS / "acompanhamento/backend", ["main", "ciclo_convocacao"])

# Só o Motor de Match tem lifespan próprio (carrega a alocação na subida --
# ver modulos/match-engine/backend/main.py). Starlette não repassa
# automaticamente o lifespan de sub-apps montados via app.mount(), então
# precisa entrar nele explicitamente aqui (padrão documentado do FastAPI
# pra combinar lifespans de sub-aplicações).
_SUB_APPS_COM_LIFESPAN = [app_match_engine]


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with AsyncExitStack() as pilha:
        for sub_app in _SUB_APPS_COM_LIFESPAN:
            await pilha.enter_async_context(sub_app.router.lifespan_context(sub_app))
        yield


app = FastAPI(title="Grupo 7 -- backend unificado (demo)", lifespan=lifespan)

app.mount("/inscricao", app_inscricao)
app.mount("/recomendacao-escolas", app_recomendacao_escolas)
app.mount("/match-engine", app_match_engine)
app.mount("/acompanhamento", app_acompanhamento)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
