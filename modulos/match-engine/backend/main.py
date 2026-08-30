"""Motor de Match -- contrato em contracts/match-engine.openapi.yaml.

A alocacao (motor.roda_matching, aceitacao diferida com reserva territorial
mole -- ver ../MATCHING.md) e calculada uma vez na subida do servidor e
mantida em memoria; toda consulta a /status/{cpf} depois so olha um
dicionario ja pronto.

Limitacoes conhecidas do contrato face aos dados reais -- ver
../README.md secao "Limitacoes conhecidas" para o porque de cada uma:
- {cpf} recebe, na pratica, o codigo aluno_anon (a base do desafio nao tem CPF real).
- StatusFila.status so usa 2 dos 4 valores do enum (Confirmado / ListaDeEspera).
- posicao_fila e a posicao na ordem de merito GLOBAL, nao por unidade.
- escola_alocada guarda so o esc_codigo (unidade); grupamento/turno nao cabem
  no contrato (additionalProperties: false).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from motor import RESERVE_FRACTION, load, ordem_global, roda_matching, soma_capacidade

# Regua legal de 2025 (Query C) -- hardcoded por decisao explicita: uma unica
# lista de criterios usada tanto aqui quanto em MATCHING.md, atualizada a mao
# se a regua mudar. Os dois ultimos sao desempate (perg_criterio='Sim'),
# nao pontuam, mas decidem a maior parte da fila -- 31,75% das criancas
# empatam em 0 pontos.
CRITERIOS = [
    {"criterio_id": "cadunico", "descricao": "Inscrito no CadÚnico (Cadastro Único para Programas Sociais)", "peso": 51},
    {"criterio_id": "educacao_especial", "descricao": "Criança público-alvo da educação especial", "peso": 25},
    {"criterio_id": "violencia_domestica", "descricao": "Criança e/ou familiar do convívio diário vítima de violência doméstica", "peso": 4},
    {"criterio_id": "familia_monoparental", "descricao": "Criança pertence a família monoparental", "peso": 4},
    {"criterio_id": "responsavel_deficiente", "descricao": "Pais/responsáveis com deficiência", "peso": 3},
    {"criterio_id": "doenca_cronica", "descricao": "Doença crônica grave na família", "peso": 3},
    {"criterio_id": "drogas_alcool", "descricao": "Uso abusivo de drogas/álcool na família", "peso": 2},
    {"criterio_id": "ex_presidiario", "descricao": "Membro da família ex-presidiário há até 5 anos", "peso": 2},
    {"criterio_id": "refugiado", "descricao": "Candidato refugiado", "peso": 2},
    {"criterio_id": "fila_ano_anterior", "descricao": "Aguardou em fila de espera no ano anterior sem ter sido atendida", "peso": 2},
    {"criterio_id": "bolsa_familia_cartao_carioca", "descricao": "Bolsa Família ou Cartão Carioca", "peso": 2},
    {"criterio_id": "irmao_na_rede", "descricao": "Possui irmão matriculado na rede pública ou parceria (desempate, não soma pontos)", "peso": 0},
    {"criterio_id": "pais_menor_18", "descricao": "Pais/responsáveis com idade menor que 18 anos (desempate, não soma pontos)", "peso": 0},
]

_estado: dict = {}


def _carrega_alocacao() -> None:
    familias, bairro_unid, capacidade, ociosas = load()
    cap_total = soma_capacidade(capacidade, ociosas)
    alocacao = roda_matching(familias, bairro_unid, cap_total, reserve_fraction=RESERVE_FRACTION)
    ordem = ordem_global(familias)
    posicao = {a: i for i, a in enumerate(ordem)}  # 0-based: posicao na ordem de merito GLOBAL

    _estado["familias"] = familias
    _estado["alocacao"] = alocacao
    _estado["posicao"] = posicao


@asynccontextmanager
async def lifespan(app: FastAPI):
    _carrega_alocacao()
    yield
    _estado.clear()


app = FastAPI(title="Motor de Match", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/criterios")
def criterios() -> list[dict]:
    return CRITERIOS


@app.get("/status/{cpf}")
def status(cpf: str) -> dict:
    # "cpf" aqui e o codigo aluno_anon -- ver limitacao no docstring do modulo.
    familias = _estado["familias"]
    fam = familias.get(cpf)
    if fam is None:
        raise HTTPException(status_code=404, detail="Nenhum status encontrado para esse CPF")

    estrato = _estado["alocacao"].get(cpf)
    if estrato is not None:
        unidade, _grupamento, _turno = estrato
        return {
            "inscricao_id": cpf,
            "status": "Confirmado",
            "posicao_fila": None,
            "escola_alocada": unidade,
            "pontuacao": fam["pontos"],
        }

    return {
        "inscricao_id": cpf,
        "status": "ListaDeEspera",
        "posicao_fila": _estado["posicao"][cpf],
        "escola_alocada": None,
        "pontuacao": fam["pontos"],
    }
