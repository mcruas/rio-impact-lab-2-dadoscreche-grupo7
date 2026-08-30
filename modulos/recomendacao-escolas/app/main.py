"""Backend de Recomendação de Escola — contrato em contracts/recomendacao-escolas.openapi.yaml.

Rodar (a partir desta pasta, modulos/recomendacao-escolas/):
    uvicorn app.main:app --reload

Não depende de nenhum outro módulo em runtime — score e histórico chegam prontos
no corpo do pedido de POST /recomendacoes (ver README.md). A única dependência de
rede externa é o ViaCEP (app/cep.py), usado só em GET /cep/{cep}.
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .cep import resolver_bairro_por_cep
from .data import Escola, buscar_por_bairro, carregar_escolas
from .distancia import EnderecoFamilia, centroides_por_bairro, distancia_mais_proxima
from .models import (
    TIPO_MORADIA,
    EnderecoRequest,
    EscolaResponse,
    HistoricoResponsavelRequest,
    PedidoRecomendacao,
    RationaleResponse,
    RecomendacaoEscolaResponse,
    ScoreEstimadoRequest,
)
from .pontuacao import montar_rationale

app = FastAPI(title="Recomendação de Escola", version="2.0.0")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

_cors_origins = os.environ.get("CORS_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_origins == "*" else _cors_origins.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

_escolas_cache: list[Escola] | None = None
_centroides_cache: dict[str, tuple[float, float]] | None = None


def _escolas() -> list[Escola]:
    global _escolas_cache
    if _escolas_cache is None:
        _escolas_cache = carregar_escolas()
    return _escolas_cache


def _centroides() -> dict[str, tuple[float, float]]:
    global _centroides_cache
    if _centroides_cache is None:
        _centroides_cache = centroides_por_bairro(_escolas())
    return _centroides_cache


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/cep/{cep}")
def cep(cep: str) -> dict[str, str]:
    bairro = resolver_bairro_por_cep(cep)
    if bairro is None:
        raise HTTPException(status_code=404, detail="CEP não encontrado")
    return {"bairro": bairro}


@app.get("/escolas", response_model=list[EscolaResponse])
def escolas(bairro: str = Query(..., min_length=1)) -> list[EscolaResponse]:
    bairro = bairro.strip()
    if not bairro:
        raise HTTPException(status_code=422, detail="bairro não pode ser vazio")
    encontradas = buscar_por_bairro(_escolas(), bairro)
    return [
        EscolaResponse(
            esc_codigo=e.esc_codigo,
            nome=e.nome,
            endereco=e.endereco,
            bairro=e.bairro,
            latitude=e.latitude,
            longitude=e.longitude,
            tipo=e.tipo,
            cod_territ=e.cod_territ,
            cre=e.cre,
        )
        for e in encontradas
    ]


def _rankear(pedido: PedidoRecomendacao, limite: int) -> list[RecomendacaoEscolaResponse]:
    enderecos_familia = [
        EnderecoFamilia(tipo=e.tipo, bairro=e.bairro) for e in pedido.enderecos
    ]
    centroides = _centroides()
    percentil = pedido.score_estimado.percentil if pedido.score_estimado else None
    vezes_convocado = (
        pedido.historico_responsavel.vezes_convocado if pedido.historico_responsavel else None
    )
    vezes_nao_compareceu = (
        pedido.historico_responsavel.vezes_nao_compareceu if pedido.historico_responsavel else None
    )

    candidatas = []
    for escola in _escolas():
        resultado = distancia_mais_proxima(enderecos_familia, centroides, escola.latitude, escola.longitude)
        if resultado is None:
            continue
        distancia_km, origem = resultado
        rationale = montar_rationale(
            distancia_km=distancia_km,
            origem_distancia=origem,
            indice_concorrencia=escola.indice_concorrencia,
            percentil_score=percentil,
            vezes_convocado=vezes_convocado,
            vezes_nao_compareceu=vezes_nao_compareceu,
        )
        candidatas.append((escola, distancia_km, origem, rationale))

    candidatas.sort(key=lambda item: item[3].pontuacao_final, reverse=True)
    selecionadas = list(candidatas[:limite])

    if pedido.escola_preferida_esc_codigo:
        ja_incluida = any(
            c[0].esc_codigo == pedido.escola_preferida_esc_codigo for c in selecionadas
        )
        if not ja_incluida:
            preferida = next(
                (c for c in candidatas if c[0].esc_codigo == pedido.escola_preferida_esc_codigo),
                None,
            )
            if preferida is not None:
                selecionadas.append(preferida)

    respostas = []
    for escola, distancia_km, origem, rationale in selecionadas:
        respostas.append(
            RecomendacaoEscolaResponse(
                esc_codigo=escola.esc_codigo,
                nome=escola.nome,
                endereco=escola.endereco,
                bairro=escola.bairro,
                latitude=escola.latitude,
                longitude=escola.longitude,
                tipo=escola.tipo,
                cod_territ=escola.cod_territ,
                cre=escola.cre,
                distancia_km=round(distancia_km, 2),
                origem_distancia=origem,
                indice_concorrencia=escola.indice_concorrencia,
                preferida=(escola.esc_codigo == pedido.escola_preferida_esc_codigo),
                pontuacao_final=round(rationale.pontuacao_final, 2),
                rationale=RationaleResponse(
                    pontos_proximidade=round(rationale.pontos_proximidade, 2),
                    pontos_adequacao_score=round(rationale.pontos_adequacao_score, 2),
                    pontos_historico=round(rationale.pontos_historico, 2),
                    explicacao=rationale.explicacao,
                ),
            )
        )
    return respostas


@app.post("/recomendacoes", response_model=list[RecomendacaoEscolaResponse])
def recomendacoes(
    pedido: PedidoRecomendacao, limite: int = Query(10, ge=1)
) -> list[RecomendacaoEscolaResponse]:
    return _rankear(pedido, limite)


@app.get("/admin/recomendacoes", response_class=HTMLResponse)
def admin_recomendacoes_form(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "admin_recomendacoes.html", {"resultados": None, "erro": None, "form": {}}
    )


@app.post("/admin/recomendacoes", response_class=HTMLResponse)
def admin_recomendacoes_submit(
    request: Request,
    bairro_moradia: str = Form(...),
    bairro_trabalho: str = Form(""),
    tipo_local_extra: str = Form(""),
    bairro_local_extra: str = Form(""),
    percentil_score: str = Form(""),
    vezes_convocado: str = Form(""),
    vezes_nao_compareceu: str = Form(""),
    escola_preferida_esc_codigo: str = Form(""),
) -> HTMLResponse:
    form_valores = {
        "bairro_moradia": bairro_moradia,
        "bairro_trabalho": bairro_trabalho,
        "tipo_local_extra": tipo_local_extra,
        "bairro_local_extra": bairro_local_extra,
        "percentil_score": percentil_score,
        "vezes_convocado": vezes_convocado,
        "vezes_nao_compareceu": vezes_nao_compareceu,
        "escola_preferida_esc_codigo": escola_preferida_esc_codigo,
    }

    enderecos = [EnderecoRequest(tipo=TIPO_MORADIA, bairro=bairro_moradia)]
    if bairro_trabalho.strip():
        enderecos.append(EnderecoRequest(tipo="Trabalho", bairro=bairro_trabalho))
    if bairro_local_extra.strip():
        enderecos.append(
            EnderecoRequest(tipo=tipo_local_extra.strip() or "Outro", bairro=bairro_local_extra)
        )

    score_estimado = None
    if percentil_score.strip():
        try:
            score_estimado = ScoreEstimadoRequest(percentil=float(percentil_score) / 100.0)
        except ValueError:
            return templates.TemplateResponse(
                request,
                "admin_recomendacoes.html",
                {"resultados": None, "erro": "Percentil de score inválido (use 0-100).", "form": form_valores},
            )

    historico_responsavel = None
    if vezes_convocado.strip():
        try:
            historico_responsavel = HistoricoResponsavelRequest(
                vezes_convocado=int(vezes_convocado),
                vezes_nao_compareceu=int(vezes_nao_compareceu or 0),
            )
        except ValueError:
            return templates.TemplateResponse(
                request,
                "admin_recomendacoes.html",
                {"resultados": None, "erro": "Histórico inválido (use números inteiros).", "form": form_valores},
            )

    try:
        pedido = PedidoRecomendacao(
            enderecos=enderecos,
            escola_preferida_esc_codigo=escola_preferida_esc_codigo.strip() or None,
            score_estimado=score_estimado,
            historico_responsavel=historico_responsavel,
        )
    except ValueError as exc:
        return templates.TemplateResponse(
            request,
            "admin_recomendacoes.html",
            {"resultados": None, "erro": str(exc), "form": form_valores},
        )

    resultados = _rankear(pedido, limite=10)
    return templates.TemplateResponse(
        request, "admin_recomendacoes.html", {"resultados": resultados, "erro": None, "form": form_valores}
    )
