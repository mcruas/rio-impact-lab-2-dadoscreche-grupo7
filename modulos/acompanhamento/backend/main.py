"""Acompanhamento -- contrato em contracts/acompanhamento.openapi.yaml.

Duas responsabilidades:
1. GET /acompanhamento/{cpf}: repassa GET /status/{cpf} do Motor de Match,
   só por HTTP (contracts/schemas/status_fila.schema.json).
2. Eixo 3 -- convocação: contato via WhatsApp/RMI pedindo ao responsável
   para confirmar uma vaga Confirmada. Este arquivo só traduz HTTP <->
   ciclo_convocacao.py, que é o dono de toda a máquina de estados (cascata
   de telefones, timeout por tentativa, liberação da vaga). Ver
   ../../../INTEGRACAO_RMI_WHATSAPP.md e ../convocacao.html para o desenho
   completo e o porquê de cada decisão.

Limitações conhecidas deste hackathon -- ver ciclo_convocacao.py e
../README.md para os porquês:
- Cascata de telefones e dígitos de CPF são simulados (a base anonimizada
  não tem CPF nem telefone reais).
- POST /convocacoes/verificar-prazos precisa ser disparado manualmente
  (curl, teste, etc.); em produção roda numa tarefa periódica.
"""
import os

import httpx
from fastapi import FastAPI, HTTPException

import ciclo_convocacao as ciclo

MATCH_ENGINE_URL = os.environ.get("MATCH_ENGINE_URL", "http://127.0.0.1:8001")

app = FastAPI(title="Acompanhamento", version="0.3.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/acompanhamento/{cpf}")
def acompanhamento(cpf: str) -> dict:
    resp = httpx.get(f"{MATCH_ENGINE_URL}/status/{cpf}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Nenhuma inscrição encontrada para esse CPF")
    resp.raise_for_status()
    return resp.json()


@app.post("/convocacoes/verificar-prazos")
def verificar_prazos() -> dict:
    """Roda o que em produção seria uma tarefa periódica (ver ciclo_convocacao.py):
    avança quem estourou o prazo de resposta e libera quem estourou o prazo do
    diretor, recalculando a alocação no Motor de Match em lote.

    Registrada ANTES de /convocacoes/{cpf} de propósito: FastAPI casa rotas na
    ordem em que são declaradas, e um path variável registrado primeiro
    engoliria "verificar-prazos" como se fosse um cpf.
    """
    timeouts = ciclo.verificar_timeouts()
    liberadas = ciclo.verificar_e_liberar(MATCH_ENGINE_URL)
    return {"timeouts_avancados": len(timeouts), "liberadas": liberadas}


@app.post("/convocacoes/{cpf}")
def criar_convocacao(cpf: str) -> dict:
    try:
        return ciclo.criar(cpf, MATCH_ENGINE_URL)
    except ciclo.NaoEncontrada:
        raise HTTPException(status_code=404, detail="Nenhuma inscrição encontrada para esse CPF")
    except ciclo.SemVagaConfirmada:
        raise HTTPException(
            status_code=409,
            detail="A criança ainda não tem vaga Confirmada no Motor de Match",
        )


@app.get("/convocacoes/{cpf}")
def consultar_convocacao(cpf: str) -> dict:
    convocacao = ciclo.consultar(cpf)
    if convocacao is None:
        raise HTTPException(status_code=404, detail="Nenhuma convocação em curso para esse CPF")
    return convocacao


@app.post("/convocacoes/{cpf}/eventos")
def registrar_evento(cpf: str, evento: dict) -> dict:
    try:
        return ciclo.registrar_evento(cpf, evento)
    except ciclo.NaoEncontrada:
        raise HTTPException(status_code=404, detail="Nenhuma convocação em curso para esse CPF")
    except ciclo.ConvocacaoEncerrada:
        raise HTTPException(
            status_code=409,
            detail="Convocação já encerrada (Confirmada, EsgotadoEscalarManual ou Liberada)",
        )
    except ciclo.IntentInvalido:
        raise HTTPException(status_code=422, detail="intent deve ser 'confirmar' ou 'nao_sou_eu'")
