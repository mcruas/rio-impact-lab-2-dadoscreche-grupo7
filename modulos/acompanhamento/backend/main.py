"""Acompanhamento -- contrato em contracts/acompanhamento.openapi.yaml.

Duas responsabilidades:
1. GET /acompanhamento/{cpf}: repassa GET /status/{cpf} do Motor de Match,
   só por HTTP (contracts/schemas/status_fila.schema.json).
2. Eixo 3 -- convocação: a máquina de estados que dispara e acompanha o
   contato via WhatsApp/RMI pedindo ao responsável para confirmar uma vaga
   Confirmada. Ver ../../../INTEGRACAO_RMI_WHATSAPP.md para o fluxo completo
   e o porquê de cada decisão.

Limitações conhecidas deste hackathon (a base anonimizada não tem CPF nem
telefone reais -- em produção isto pluga no RMI de verdade, ver o doc acima):
- A cascata de telefones do RMI é simulada por TELEFONES_POR_CRIANCA
  telefones numerados por índice, não os telefones reais da pessoa_fisica.
- Os "últimos 4 dígitos do CPF" usados para autenticar a confirmação são
  gerados de forma determinística a partir do código anonimizado, não são
  dígitos de CPF de verdade.
- O disparo do HSM em si (Wetalkie) e o LLM que interpreta a resposta não
  são chamados -- este módulo só implementa o webhook que os receberia
  (POST /convocacoes/{cpf}/eventos) e o gatilho que os acionaria
  (POST /convocacoes/{cpf}).
"""
import hashlib
import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

MATCH_ENGINE_URL = os.environ.get("MATCH_ENGINE_URL", "http://127.0.0.1:8001")

# Quantos telefones a cascata do RMI teria para uma família nesta simulação.
# Em produção isto é o tamanho real da lista telefone_qualidade/confianca_propriedade
# filtrada por estrategia_envio IN ('ENVIAR','TESTAR') -- varia por pessoa.
TELEFONES_POR_CRIANCA = 3

app = FastAPI(title="Acompanhamento", version="0.2.0")

_convocacoes: dict[str, dict] = {}


def _agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cpf_digitos_esperado(cpf: str) -> str:
    """Simula os últimos 4 dígitos do CPF da criança para autenticar a confirmação.

    Determinístico a partir do código anonimizado só para esta demo -- em
    produção é o dado real trazido pelo RMI (rj-crm-registry...pessoa_fisica).
    """
    return hashlib.sha256(cpf.encode()).hexdigest()[:4].upper()


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


@app.post("/convocacoes/{cpf}")
def criar_convocacao(cpf: str) -> dict:
    existente = _convocacoes.get(cpf)
    if existente is not None:
        return existente

    resp = httpx.get(f"{MATCH_ENGINE_URL}/status/{cpf}")
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Nenhuma inscrição encontrada para esse CPF")
    resp.raise_for_status()
    status_fila = resp.json()
    if status_fila["status"] != "Confirmado":
        raise HTTPException(
            status_code=409,
            detail="A criança ainda não tem vaga Confirmada no Motor de Match",
        )

    convocacao = {
        "inscricao_id": cpf,
        "estado": "AguardandoResposta",
        "indice_telefone": 0,
        "tentativas": 0,
        "atualizado_em": _agora(),
    }
    _convocacoes[cpf] = convocacao
    return convocacao


@app.get("/convocacoes/{cpf}")
def consultar_convocacao(cpf: str) -> dict:
    convocacao = _convocacoes.get(cpf)
    if convocacao is None:
        raise HTTPException(status_code=404, detail="Nenhuma convocação em curso para esse CPF")
    return convocacao


@app.post("/convocacoes/{cpf}/eventos")
def registrar_evento(cpf: str, evento: dict) -> dict:
    convocacao = _convocacoes.get(cpf)
    if convocacao is None:
        raise HTTPException(status_code=404, detail="Nenhuma convocação em curso para esse CPF")
    if convocacao["estado"] != "AguardandoResposta":
        raise HTTPException(
            status_code=409,
            detail="Convocação já encerrada (Confirmada ou EsgotadoEscalarManual)",
        )

    intent = evento.get("intent")
    if intent not in ("confirmar", "nao_sou_eu"):
        raise HTTPException(status_code=422, detail="intent deve ser 'confirmar' ou 'nao_sou_eu'")

    autenticado = intent == "confirmar" and evento.get("cpf_digitos") == _cpf_digitos_esperado(cpf)

    if autenticado:
        convocacao["estado"] = "Confirmada"
    else:
        # nao_sou_eu, ou "confirmar" com dígitos errados (número reciclado/
        # compartilhado -- tratado igual, a cascata avança do mesmo jeito).
        convocacao["tentativas"] += 1
        convocacao["indice_telefone"] += 1
        if convocacao["indice_telefone"] >= TELEFONES_POR_CRIANCA:
            convocacao["estado"] = "EsgotadoEscalarManual"

    convocacao["atualizado_em"] = _agora()
    return convocacao
