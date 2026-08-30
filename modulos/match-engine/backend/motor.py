#!/usr/bin/env python3
"""
Aceitacao diferida (Gale-Shapley, proposta pelas criancas) com assentos de
prioridade especifica por estrato (unidade, grupamento, turno): assentos
"abertos" ordenados pela regua legal (pontuacao + desempate), assentos
"reservados" ao territorio processados depois, com reserva MOLE -- se nao
houver demanda local suficiente, o assento reservado aceita nao-locais em
vez de ficar vazio.

Por que uma rodada de DA e nao tres passes sequenciais: com tres passes,
uma crianca alocada numa opcao pior no passe 1 nunca e reconsiderada para
uma vaga reservada melhor no passe 2, mesmo sendo do territorio e elegivel.
Isso desperdica vaga reservada E deixa de ser a prova de estrategia (truncar
a lista pode melhorar o resultado da crianca). DA com proposta e rejeicao
resolve os dois problemas: uma crianca so fica definitivamente fora de uma
unidade quando e rejeitada por ela, e pode ser deslocada e voltar a propor
adiante enquanto ainda houver rodada.

Capacidade por estrato = numero de criancas efetivamente CONFIRMADAS no
processo real de 2025 nesse estrato (a MELHOR situacao entre as linhas de
opcao da crianca naquele estrato -- ver PRIORIDADE_SITUACAO. Uma crianca com
mais de uma linha para o mesmo estrato, uma "Confirmado" e outra
"Cancelado pelo sistema", tem o registro real de fato Confirmado; manter so
a ultima linha lida do CSV, como a versao anterior deste script fazia,
subestimava a capacidade real em ~530 vagas).
"""
import csv, hashlib, os
from collections import defaultdict
from datetime import datetime

DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
RESERVE_FRACTION = 0.35  # fracao de vagas reservadas ao territorio (bairro da unidade)

# menor numero = situacao mais favoravel para a crianca
PRIORIDADE_SITUACAO = {
    "Confirmado": 0,
    "Selecionado": 1,
    "Selecionado da lista": 1,
    "Ativo": 2,
    "Lista de espera": 3,
    "Cancelado na confirmacao": 4,
    "Cancelado pelo sistema": 5,
    "Cancelado": 6,
}


def load():
    familias = {}  # aluno_anon -> {"pontos":..., "bairro":..., "opcoes":[(opcao,unidade,g,h), ...]}
    with open(f"{DADOS}/match_opcoes.csv", encoding="utf8") as f:
        for row in csv.DictReader(f):
            a = row["aluno_anon"]
            if a not in familias:
                familias[a] = {
                    "pontos": int(row["pontos"]),
                    "irmao": int(row["irmao"]),
                    "pais_menor18": int(row["pais_menor18"]),
                    "bairro": row["bairro_fam"], "opcoes": [], "situacao_real": {},
                }
            familias[a]["opcoes"].append((int(row["opcao"]), row["unidade"], row["g"], row["h"]))

            estrato = (row["unidade"], row["g"], row["h"])
            situ = row["situacao"]
            atual = familias[a]["situacao_real"].get(estrato)
            if atual is None or PRIORIDADE_SITUACAO.get(situ, 99) < PRIORIDADE_SITUACAO.get(atual, 99):
                familias[a]["situacao_real"][estrato] = situ
    for a in familias:
        familias[a]["opcoes"].sort()  # respeita a ordem de preferencia declarada

    bairro_unid = {}
    with open(f"{DADOS}/match_unidades.csv", encoding="utf8") as f:
        for row in csv.DictReader(f):
            bairro_unid[row["unidade"]] = row["bairro_unid"]

    capacidade = {}
    with open(f"{DADOS}/match_capacidade.csv", encoding="utf8") as f:
        for row in csv.DictReader(f):
            capacidade[row["unidade"], row["g"], row["h"]] = int(row["capacidade"])

    ociosas = {}
    with open(f"{DADOS}/match_ociosas.csv", encoding="utf8") as f:
        for row in csv.DictReader(f):
            ociosas[row["unidade"], row["g"], row["h"]] = int(float(row["ociosas"]))

    return familias, bairro_unid, capacidade, ociosas


def ordem_global(familias):
    """Ordem legal completa: pontuacao > desempates legais > sorteio.

    Os dois desempates (irmao matriculado na rede, pais/responsaveis
    menores de 18 anos) vem da Query C com perg_criterio='Sim' -- sao
    criterios de prioridade, nao pontuados, e valem nos 5 anos da base
    (2021-2025). Sorteio: hash com semente fixa e publica, unico por
    crianca (single tie-breaking), nunca reaproveitada entre processos.
    """
    def chave(a):
        f = familias[a]
        h = hashlib.sha256(f"SEMENTE-PUBLICA-2025|{a}".encode()).hexdigest()
        return (-f["pontos"], -f["irmao"], -f["pais_menor18"], h)
    return sorted(familias.keys(), key=chave)


def _escolhe(estrato, candidatos, aberta_cap, reservada_cap, bairro_unid, familias, ordem_pos):
    """Funcao de escolha da unidade para um estrato: quem fica retido, dado o
    conjunto de candidatos (retidos da rodada anterior + novas propostas).
    Assentos abertos primeiro (ordem global), depois reservados (locais
    primeiro, no-locais preenchem o que sobrar -- reserva mole)."""
    unidade = estrato[0]
    bairro_unidade = bairro_unid.get(unidade)
    ordenados = sorted(candidatos, key=lambda a: ordem_pos[a])

    abertos = ordenados[:aberta_cap]
    resto = ordenados[aberta_cap:]
    locais = [a for a in resto if familias[a]["bairro"] == bairro_unidade]
    nao_locais = [a for a in resto if familias[a]["bairro"] != bairro_unidade]
    reservados = (locais + nao_locais)[:reservada_cap]

    return set(abertos) | set(reservados)


def roda_matching(familias, bairro_unid, capacidade, reserve_fraction=RESERVE_FRACTION):
    ordem = ordem_global(familias)
    ordem_pos = {a: i for i, a in enumerate(ordem)}

    aberta_cap, reservada_cap = {}, {}
    for estrato, cap in capacidade.items():
        r = round(cap * reserve_fraction)
        reservada_cap[estrato] = r
        aberta_cap[estrato] = cap - r

    proximo_idx = {a: 0 for a in familias}  # proxima opcao (indice) a propor
    held = defaultdict(set)                 # estrato -> conjunto de retidos AGORA (fonte da verdade)

    livres = set(familias.keys())
    while livres:
        propostas = defaultdict(set)
        for a in livres:
            opcoes = familias[a]["opcoes"]
            idx = proximo_idx[a]
            if idx >= len(opcoes):
                continue  # esgotou a lista, fica definitivamente sem vaga
            _, unidade, g, h = opcoes[idx]
            propostas[unidade, g, h].add(a)
            proximo_idx[a] = idx + 1

        if not propostas:
            break

        novos_livres = set()
        for estrato, novos in propostas.items():
            candidatos = held[estrato] | novos
            escolhidos = _escolhe(estrato, candidatos, aberta_cap.get(estrato, 0),
                                   reservada_cap.get(estrato, 0), bairro_unid, familias, ordem_pos)
            for a in candidatos - escolhidos:
                novos_livres.add(a)  # rejeitado (novo ou deslocado), volta a propor
            held[estrato] = escolhidos

        livres = novos_livres

    # a alocacao final e o ultimo estado de "held", nao um rastro incremental --
    # uma crianca aceita e depois deslocada, sem conseguir vaga em outro lugar,
    # nao pode aparecer como alocada em lugar nenhum.
    alocacao = {}
    for estrato, alunos in held.items():
        for a in alunos:
            alocacao[a] = estrato
    return {a: alocacao.get(a) for a in familias}


def relatorio(familias, alocacao, label):
    n = len(familias)
    matched = sum(1 for a in alocacao.values() if a is not None)
    print(f"\n=== {label} ===")
    print(f"criancas no processo:      {n:>7,}")
    print(f"alocadas (nova regra):     {matched:>7,}  ({100*matched/n:.1f}%)")
    print(f"sem vaga (nova regra):     {n-matched:>7,}  ({100*(n-matched)/n:.1f}%)")

    real_confirmado = sum(1 for f in familias.values() if any(s == "Confirmado" for s in f["situacao_real"].values()))
    print(f"confirmadas no real 2025:  {real_confirmado:>7,}  ({100*real_confirmado/n:.1f}%)")

    ganharam = sum(1 for a, f in familias.items()
                    if alocacao.get(a) and not any(s == "Confirmado" for s in f["situacao_real"].values()))
    print(f"GANHARAM vaga que nao tinham: {ganharam:>7,}")

    op1 = [a for a, f in familias.items() if len(f["opcoes"]) == 1]
    op1_ganharam = sum(1 for a in op1 if alocacao.get(a) and not any(s == "Confirmado" for s in familias[a]["situacao_real"].values()))
    print(f"  das quais, opcao unica:     {op1_ganharam:>7,}  (de {len(op1):,} familias de opcao unica)")

    perderam = sum(1 for a, f in familias.items()
                    if any(s == "Confirmado" for s in f["situacao_real"].values()) and not alocacao.get(a))
    print(f"PERDERAM vaga que tinham:     {perderam:>7,}")


def soma_capacidade(capacidade, ociosas):
    total = dict(capacidade)
    for estrato, oc in ociosas.items():
        total[estrato] = total.get(estrato, 0) + oc
    return total


# Situacao "resolvida" para fins de P4: uma opcao ofertada (Selecionado/
# Selecionado da lista) enquanto outra segue em Lista de espera -- a mesma
# definicao usada na tabela de PROBLEMAS.md P4. Nao inclui "Confirmado" de
# proposito: cadastro Confirmado numa opcao e Lista de espera noutra e uma
# situacao normal de quem confirmou e nao cancelou as demais, nao o
# fenomeno que P4 descreve.
SITUACOES_RESOLVIDAS = {"Selecionado", "Selecionado da lista"}


def carrega_vagas_selecionadas():
    """Cadastros com uma opcao em 'Selecionado'/'Selecionado da lista' no
    processo real de 2025, com a data de CRIACAO DO CADASTRO (nao a data em
    que a opcao virou Selecionado -- a base nao registra isso, ver
    PROBLEMAS.md P6). dados/vagas_selecionadas.csv foi gerado a partir da
    Query A bruta por dados/gerar_vagas_selecionadas.sql -- nao depende da
    base bruta em tempo de execucao, so para regenerar do zero.
    """
    vagas = []
    with open(f"{DADOS}/vagas_selecionadas.csv", encoding="utf8") as f:
        for row in csv.DictReader(f):
            vagas.append({
                "inscricao_id": row["aluno_anon"],
                "opcao": int(row["opcao"]),
                "unidade": row["unidade"],
                "situacao": row["situacao"],
                "data_criacao": _parse_data_criacao(row["data_criacao"]),
            })
    return vagas


def _parse_data_criacao(valor: str) -> datetime:
    for formato in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(valor.strip(), formato)
        except ValueError:
            continue
    raise ValueError(f"formato de data_criacao nao reconhecido: {valor!r}")


def detecta_inconsistencias(familias):
    """Cadastros onde uma opcao esta resolvida (Confirmado/Selecionado/
    Selecionado da lista) e outra opcao do MESMO cadastro segue em Lista de
    espera -- confuso para quem acompanha linha a linha, porque o cadastro
    parece "ainda pendente" quando na verdade uma das opcoes ja tem
    desfecho. So enxerga isso quem compara as opcoes de um mesmo cadastro
    entre si, nao quem le uma linha por vez (PROBLEMAS.md P4).
    """
    inconsistencias = []
    for a, f in familias.items():
        situacoes = f["situacao_real"]  # estrato -> situacao (ja deduplicado por load())
        tem_resolvida = any(s in SITUACOES_RESOLVIDAS for s in situacoes.values())
        tem_espera = any(s == "Lista de espera" for s in situacoes.values())
        if tem_resolvida and tem_espera:
            inconsistencias.append({
                "inscricao_id": a,
                "opcoes": [
                    {"unidade": estrato[0], "situacao": situ}
                    for estrato, situ in situacoes.items()
                ],
            })
    return inconsistencias


if __name__ == "__main__":
    familias, bairro_unid, capacidade, ociosas = load()
    print(f"familias carregadas: {len(familias):,}")
    print(f"unidades com bairro: {len(bairro_unid):,}")
    print(f"estratos com capacidade (=confirmados reais 2025): {len(capacidade):,}  total vagas={sum(capacidade.values()):,}")
    print(f"vagas ociosas conhecidas (arquivo de oferta):        total={sum(ociosas.values()):,}")

    print("\n" + "#"*78)
    print(f"# CENARIO A -- mesma capacidade que existiu de fato (redistribuicao justa)")
    print("#"*78)
    aloc = roda_matching(familias, bairro_unid, capacidade)
    relatorio(familias, aloc, f"Reserva territorial {int(RESERVE_FRACTION*100)}% (DA, 1 rodada)")

    aloc0 = roda_matching(familias, bairro_unid, capacidade, reserve_fraction=0.0)
    relatorio(familias, aloc0, "Sem reserva territorial (so merito, 0%)")

    print("\n" + "#"*78)
    print("# CENARIO B -- capacidade real + vaga ociosa hoje sem uso (ganho liquido)")
    print("#"*78)
    cap_b = soma_capacidade(capacidade, ociosas)
    alocB = roda_matching(familias, bairro_unid, cap_b)
    relatorio(familias, alocB, f"Reserva territorial {int(RESERVE_FRACTION*100)}% + vaga ociosa (DA, 1 rodada)")
