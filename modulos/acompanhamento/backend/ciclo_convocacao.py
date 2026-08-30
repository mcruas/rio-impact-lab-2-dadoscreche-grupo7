"""Maquina de estados da convocacao (Eixo 3) -- separado de main.py de
proposito: main.py so traduz HTTP <-> estas funcoes, toda a logica de ciclo
de vida mora aqui. Ver ../../../INTEGRACAO_RMI_WHATSAPP.md e
../convocacao.html para o desenho completo e o porque de cada prazo.

Duas rotinas cobrem quem nunca confirma (silencio, nao so recusa
explicita):
- verificar_timeouts(): sem resposta dentro do prazo por tentativa tem a
  mesma consequencia de um "nao sou eu" explicito -- avanca a cascata.
- verificar_e_liberar(): se o prazo do proprio fluxo manual do diretor
  tambem vence, marca a convocacao como Liberada e chama o Motor de Match
  (POST /nao-confirmados, em lote -- nunca uma chamada por crianca) para
  recalcular a alocacao. A vaga passa para quem tinha a proxima prioridade
  naquele estrato, pela mesma ordem de merito de sempre.

Em producao estas duas rotinas rodariam numa tarefa periodica (cron/
Prefect); aqui sao expostas como POST /convocacoes/verificar-prazos, para
poder demonstrar o ciclo inteiro sem esperar os prazos reais passarem.
"""
import hashlib
from datetime import datetime, timedelta, timezone

import httpx

TELEFONES_POR_CRIANCA = 3
PRAZO_TENTATIVA = timedelta(hours=48)
PRAZO_DIRETOR = timedelta(days=5)

_convocacoes: dict[str, dict] = {}


class NaoEncontrada(Exception):
    """Nenhuma inscrição encontrada para esse CPF no Motor de Match."""


class SemVagaConfirmada(Exception):
    """A criança ainda não tem vaga Confirmada no Motor de Match."""


class ConvocacaoEncerrada(Exception):
    """Convocação já está em um estado final (Confirmada, EsgotadoEscalarManual ou Liberada)."""


class IntentInvalido(Exception):
    """intent do evento não é 'confirmar' nem 'nao_sou_eu'."""


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(momento: datetime) -> str:
    return momento.isoformat()


def _cpf_digitos_esperado(cpf: str) -> str:
    """Simula os últimos 4 dígitos do CPF da criança para autenticar a confirmação.

    Determinístico a partir do código anonimizado só para esta demo -- em
    produção é o dado real trazido pelo RMI (rj-crm-registry...pessoa_fisica).
    """
    return hashlib.sha256(cpf.encode()).hexdigest()[:4].upper()


def criar(cpf: str, match_engine_url: str) -> dict:
    existente = _convocacoes.get(cpf)
    if existente is not None:
        return existente

    resp = httpx.get(f"{match_engine_url}/status/{cpf}")
    if resp.status_code == 404:
        raise NaoEncontrada()
    resp.raise_for_status()
    if resp.json()["status"] != "Confirmado":
        raise SemVagaConfirmada()

    convocacao = {
        "inscricao_id": cpf,
        "estado": "AguardandoResposta",
        "indice_telefone": 0,
        "tentativas": 0,
        "atualizado_em": _iso(_agora()),
    }
    _convocacoes[cpf] = convocacao
    return convocacao


def consultar(cpf: str) -> dict | None:
    return _convocacoes.get(cpf)


def _avanca_cascata(convocacao: dict) -> None:
    convocacao["tentativas"] += 1
    convocacao["indice_telefone"] += 1
    if convocacao["indice_telefone"] >= TELEFONES_POR_CRIANCA:
        convocacao["estado"] = "EsgotadoEscalarManual"
    convocacao["atualizado_em"] = _iso(_agora())


def registrar_evento(cpf: str, evento: dict) -> dict:
    convocacao = _convocacoes.get(cpf)
    if convocacao is None:
        raise NaoEncontrada()
    if convocacao["estado"] != "AguardandoResposta":
        raise ConvocacaoEncerrada()

    intent = evento.get("intent")
    if intent not in ("confirmar", "nao_sou_eu"):
        raise IntentInvalido()

    autenticado = intent == "confirmar" and evento.get("cpf_digitos") == _cpf_digitos_esperado(cpf)
    if autenticado:
        convocacao["estado"] = "Confirmada"
        convocacao["atualizado_em"] = _iso(_agora())
    else:
        # nao_sou_eu, ou "confirmar" com digitos errados (numero reciclado/
        # compartilhado -- tratado igual, a cascata avanca do mesmo jeito).
        _avanca_cascata(convocacao)
    return convocacao


def verificar_timeouts() -> list[dict]:
    """Silêncio além do prazo por tentativa tem a mesma consequência de um
    "não sou eu" explícito -- ninguém fica esperando resposta pra sempre.
    """
    agora = _agora()
    avancadas = []
    for convocacao in _convocacoes.values():
        if convocacao["estado"] != "AguardandoResposta":
            continue
        atualizado = datetime.fromisoformat(convocacao["atualizado_em"])
        if agora - atualizado >= PRAZO_TENTATIVA:
            _avanca_cascata(convocacao)
            avancadas.append(convocacao)
    return avancadas


def verificar_e_liberar(match_engine_url: str) -> list[dict]:
    """Prazo do fluxo manual do diretor também vencido: libera a vaga.

    Chama o Motor de Match em lote (nunca uma chamada por criança -- ver o
    docstring do módulo) para recalcular a alocação excluindo quem está
    sendo liberado agora.
    """
    agora = _agora()
    a_liberar = [
        c
        for c in _convocacoes.values()
        if c["estado"] == "EsgotadoEscalarManual"
        and agora - datetime.fromisoformat(c["atualizado_em"]) >= PRAZO_DIRETOR
    ]
    if not a_liberar:
        return []

    cpfs = [c["inscricao_id"] for c in a_liberar]
    resp = httpx.post(f"{match_engine_url}/nao-confirmados", json={"cpfs": cpfs})
    resp.raise_for_status()

    for convocacao in a_liberar:
        convocacao["estado"] = "Liberada"
        convocacao["atualizado_em"] = _iso(agora)
    return a_liberar
