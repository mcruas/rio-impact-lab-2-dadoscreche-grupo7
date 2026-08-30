"""
Investigacao de H6 (atrito/cancelamentos no funil) e H12 (efetividade da pontuacao)
a partir das bases em 'desafio/Bases IC_ ClassificadoseFila/'.

Roda checagens de qualidade de dado ANTES de responder as hipoteses (chave
duplicada, valores fora do esperado, nulos mal codificados, outliers de
pontuacao e de identidade), e aplica as correcoes encontradas:

  1. CEP/bairro usam a string literal "NULL" para ausencia (nao NULL de
     verdade) -- precisa de NULLIF(col,'NULL') antes de qualquer contagem.
  2. `aluno_anon` tem ~696 codigos "bucket" (mais de 1 nascimento_aluno_anomes
     distinto sob o mesmo codigo) que representam criancas nao identificaveis
     agrupadas sob o mesmo codigo, nao uma crianca real -- precisam ser
     excluidos de qualquer analise por crianca.
  3. A pontuacao valida por pergunta so deve contar quando resposta='Sim' E
     confirmado='Sim' (declarado E validado) -- usar so confirmado='Sim'
     conta indevidamente casos de "resposta Nao confirmada", inflando o score.
  4. A taxa de confirmado='Sim' dado resposta='Sim' cai de ~89% em 2021 para
     ~8-11% de 2022 em diante -- indica mudanca de definicao/processo de
     validacao entre 2021 e 2022, nao so a mudanca de regua 2023->2024 ja
     documentada. 2021 deve ser tratado separadamente em comparacoes de score.

Uso: python eda/investigar_h6_h12.py  (executar a partir da raiz do repositorio)
"""
import duckdb

BASE = "desafio/Bases IC_ ClassificadoseFila"
A = f"{BASE}/01_QueryA_InscricoesPorAno.csv.gz"
B = f"{BASE}/02_QueryB_RespostasSocioEconomicas.csv.gz"
C = f"{BASE}/03_QueryC_PerguntasComDescricao.csv"

con = duckdb.connect()
con.execute(f"CREATE OR REPLACE VIEW a_raw AS SELECT * FROM read_csv_auto('{A}', delim=';', header=True)")
con.execute(f"CREATE OR REPLACE VIEW b AS SELECT * FROM read_csv_auto('{B}', delim=';', header=True)")
con.execute(f"CREATE OR REPLACE VIEW c AS SELECT * FROM read_csv_auto('{C}', delim=';', header=True)")

# 'a' corrige NULL-como-string em CEP/bairro
con.execute("""
    CREATE OR REPLACE VIEW a AS
    SELECT * EXCLUDE (CEP, bairro),
           NULLIF(CEP, 'NULL') AS CEP,
           NULLIF(bairro, 'NULL') AS bairro
    FROM a_raw
""")

# aluno_anon "bucket" = mais de 1 data de nascimento distinta sob o mesmo codigo
con.execute("""
    CREATE OR REPLACE VIEW aluno_bucket AS
    SELECT aluno_anon
    FROM a
    GROUP BY 1
    HAVING COUNT(DISTINCT nascimento_aluno_anomes) > 1
""")


def section(title):
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def run(label, sql):
    print(f"\n--- {label} ---")
    rows = con.execute(sql).fetchall()
    cols = [d[0] for d in con.description]
    print(cols)
    for r in rows:
        print(r)
    return rows


# ---------------------------------------------------------------------------
section("PARTE 0 — QUALIDADE DE DADO (achados e correcoes)")
# ---------------------------------------------------------------------------

run("CEP/bairro nulos apos corrigir a string 'NULL' (deve bater com o dicionario: ~23.617 / ~23.725)", """
    SELECT
      SUM(CASE WHEN CEP IS NULL THEN 1 ELSE 0 END) AS null_cep,
      SUM(CASE WHEN bairro IS NULL THEN 1 ELSE 0 END) AS null_bairro,
      COUNT(*) AS total
    FROM a
""")

run("aluno_anon 'bucket' (codigo compartilhado por varias criancas distintas)", """
    SELECT COUNT(*) AS n_codigos_bucket FROM aluno_bucket
""")
run("linhas de A afetadas pelos codigos bucket", """
    SELECT COUNT(*) FROM a WHERE aluno_anon IN (SELECT aluno_anon FROM aluno_bucket)
""")
run("top 5 codigos bucket (ilustra o problema)", """
    SELECT aluno_anon, COUNT(*) n_linhas, COUNT(DISTINCT nascimento_aluno_anomes) n_datas_distintas,
           COUNT(DISTINCT responsavel_anon) n_responsaveis_distintos
    FROM a WHERE aluno_anon IN (SELECT aluno_anon FROM aluno_bucket)
    GROUP BY 1 ORDER BY n_linhas DESC LIMIT 5
""")

run("data_criacao: linhas com ano_data_criacao >= ano_processo + 2 (fora da janela esperada)", """
    SELECT ano, EXTRACT(year FROM data_criacao) AS ano_dc, COUNT(*) n
    FROM a WHERE EXTRACT(year FROM data_criacao) >= ano + 2
    GROUP BY 1,2 ORDER BY 1,2
""")

run("B: taxa de confirmado=Sim dado resposta=Sim, por ano (quebra de definicao/processo)", """
    SELECT ano,
      ROUND(100.0*SUM(CASE WHEN resposta='Sim' AND confirmado='Sim' THEN 1 ELSE 0 END)
            / NULLIF(SUM(CASE WHEN resposta='Sim' THEN 1 ELSE 0 END),0), 1) AS pct_confirmado_dado_sim
    FROM b GROUP BY 1 ORDER BY 1
""")


# ---------------------------------------------------------------------------
section("PARTE 1 — H6: ATRITO E CANCELAMENTOS NO FUNIL")
# ---------------------------------------------------------------------------

con.execute("""
    CREATE OR REPLACE VIEW insc AS
    SELECT ano, prm_id, plm_id, ipl_id,
      COUNT(*) AS n_opcoes,
      MAX(CASE WHEN situacao IN ('Confirmado','Ativo','Selecionado','Selecionado da lista') THEN 1 ELSE 0 END) AS atendida,
      MAX(CASE WHEN situacao = 'Lista de espera' THEN 1 ELSE 0 END) AS em_fila,
      MAX(CASE WHEN situacao = 'Cancelado pelo sistema' THEN 1 ELSE 0 END) AS teve_cancel_sistema,
      MAX(CASE WHEN situacao = 'Cancelado na confirmacao' THEN 1 ELSE 0 END) AS teve_cancel_confirmacao,
      MAX(CASE WHEN situacao = 'Cancelado' THEN 1 ELSE 0 END) AS teve_cancel_simples
    FROM a
    GROUP BY 1,2,3,4
""")

run("H6.1 — situacao geral (837.179 linhas, conferido com o dicionario)", """
    SELECT situacao, COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) pct
    FROM a GROUP BY 1 ORDER BY n DESC
""")

run("H6.2 — situacao por posicao da opcao", """
    SELECT
      CASE WHEN opcao = 1 THEN '1a opcao' WHEN opcao = 2 THEN '2a opcao' ELSE '3a+ opcao' END AS grupo_opcao,
      situacao, COUNT(*) n
    FROM a GROUP BY 1,2 ORDER BY 1, n DESC
""")

run("H6.3 — % Cancelado pelo sistema por ano", """
    SELECT ano, COUNT(*) total,
      SUM(CASE WHEN situacao='Cancelado pelo sistema' THEN 1 ELSE 0 END) AS n_cancel_sistema,
      ROUND(100.0*SUM(CASE WHEN situacao='Cancelado pelo sistema' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct
    FROM a GROUP BY 1 ORDER BY 1
""")

run("H6.4 — desfecho consolidado por inscricao (343.308 inscricoes)", """
    SELECT
      CASE WHEN atendida=1 THEN 'Atendida'
           WHEN em_fila=1 THEN 'Fila (sem atendimento)'
           ELSE 'Cancelada (sem atendimento nem fila)' END AS desfecho,
      COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) pct
    FROM insc GROUP BY 1 ORDER BY n DESC
""")

run("H6.5 — entre quem teve 'Cancelado pelo sistema' em alguma opcao, desfecho final", """
    SELECT
      CASE WHEN atendida=1 THEN 'Atendida em outra opcao'
           WHEN em_fila=1 THEN 'Ficou em fila'
           ELSE 'Perda total' END AS desfecho,
      COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) pct
    FROM insc WHERE teve_cancel_sistema = 1 GROUP BY 1 ORDER BY n DESC
""")

run("H6.6 — numero de opcoes por inscricao vs taxa de atendimento (refuta ou confirma H11)", """
    SELECT n_opcoes, COUNT(*) AS n_inscricoes, ROUND(100.0*SUM(atendida)/COUNT(*),1) AS pct_atendida
    FROM insc GROUP BY 1 ORDER BY 1
""")

run("H6.7 — criancas (aluno_anon, excluindo codigos bucket) com mais de 1 inscricao no mesmo ano", """
    SELECT n_inscricoes_no_ano, COUNT(*) AS n_criancas FROM (
        SELECT ano, aluno_anon, COUNT(DISTINCT prm_id||'-'||plm_id||'-'||ipl_id) AS n_inscricoes_no_ano
        FROM a
        WHERE aluno_anon IS NOT NULL AND aluno_anon NOT IN (SELECT aluno_anon FROM aluno_bucket)
        GROUP BY 1,2
    )
    GROUP BY 1 ORDER BY 1
""")

run("H6.8 — criancas (excluindo bucket) que reaparecem em mais de 1 ano, e taxa de perda total recorrente", """
    WITH crianca_ano AS (
        SELECT DISTINCT aluno_anon, ano FROM a
        WHERE aluno_anon IS NOT NULL AND aluno_anon NOT IN (SELECT aluno_anon FROM aluno_bucket)
    ),
    n_anos AS (SELECT aluno_anon, COUNT(*) AS n_anos FROM crianca_ano GROUP BY 1)
    SELECT n_anos, COUNT(*) AS n_criancas FROM n_anos GROUP BY 1 ORDER BY 1
""")


# ---------------------------------------------------------------------------
section("PARTE 2 — H12: EFETIVIDADE DA PONTUACAO DE CLASSIFICACAO (score corrigido)")
# ---------------------------------------------------------------------------

con.execute("""
    CREATE OR REPLACE VIEW score AS
    SELECT b.ano, b.prm_id, b.plm_id, b.ipl_id,
      SUM(CASE WHEN b.resposta='Sim' AND b.confirmado='Sim' THEN c.perg_pontuacao ELSE 0 END) AS score_valido
    FROM b JOIN c ON c.ano = b.ano AND c.ich_perg_id = b.ich_perg_id
    GROUP BY 1,2,3,4
""")

run("H12.1 — outliers: inscricao com score acima do maximo teorico do ano", """
    SELECT s.ano, COUNT(*) AS n_acima_do_maximo
    FROM score s JOIN (SELECT ano, SUM(perg_pontuacao) AS maximo FROM c GROUP BY 1) m ON m.ano = s.ano
    WHERE s.score_valido > m.maximo GROUP BY 1
""")

run("H12.2 — % de inscricoes com score_valido = 0, por ano (zero-inflation)", """
    SELECT ano, COUNT(*) total, ROUND(100.0*SUM(CASE WHEN score_valido=0 THEN 1 ELSE 0 END)/COUNT(*),1) pct_zero
    FROM score GROUP BY 1 ORDER BY 1
""")

run("H12.3 — inscricoes em A sem nenhuma linha em B (sem score) e seu desfecho", """
    SELECT
      CASE WHEN i.atendida=1 THEN 'Atendida' WHEN i.em_fila=1 THEN 'Fila' ELSE 'Cancelada' END AS desfecho,
      COUNT(*) n
    FROM insc i
    WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.prm_id=i.prm_id AND b.plm_id=i.plm_id AND b.ipl_id=i.ipl_id)
    GROUP BY 1 ORDER BY n DESC
""")

run("H12.4 — % com score_valido>0 por desfecho e por ano (comparacao robusta a zero-inflation)", """
    SELECT i.ano,
      CASE WHEN i.atendida=1 THEN 'Atendida' WHEN i.em_fila=1 THEN 'Fila' ELSE 'Cancelada' END desfecho,
      COUNT(*) n,
      ROUND(100.0*SUM(CASE WHEN s.score_valido>0 THEN 1 ELSE 0 END)/COUNT(*),1) pct_score_positivo,
      ROUND(AVG(CASE WHEN s.score_valido>0 THEN s.score_valido END),1) media_dado_positivo
    FROM insc i JOIN score s USING(ano,prm_id,plm_id,ipl_id)
    GROUP BY 1,2 ORDER BY 1, pct_score_positivo DESC
""")

# ---------------------------------------------------------------------------
section("PARTE 3 — APROFUNDAMENTO DA PERDA TOTAL, FOCO 2024-2025")
# ---------------------------------------------------------------------------
# Anos recentes = regua de pontuacao atual, mais acionavel para recomendacao.

ANOS_RECENTES = "(2024,2025)"

run("3.1 — funil geral, 2024-2025 combinado", f"""
    SELECT
      CASE WHEN atendida=1 THEN 'Atendida' WHEN em_fila=1 THEN 'Fila' ELSE 'Perda total' END desfecho,
      COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) pct
    FROM insc WHERE ano IN {ANOS_RECENTES} GROUP BY 1 ORDER BY n DESC
""")

run("3.2 — assinatura de cancelamento na perda total, 2024-2025 combinado", f"""
    SELECT
      CASE WHEN teve_cancel_sistema=1 AND teve_cancel_confirmacao=0 AND teve_cancel_simples=0 THEN 'So sistema'
           WHEN teve_cancel_sistema=0 AND teve_cancel_confirmacao=1 AND teve_cancel_simples=0 THEN 'So confirmacao'
           WHEN teve_cancel_sistema=0 AND teve_cancel_confirmacao=0 AND teve_cancel_simples=1 THEN 'So simples'
           ELSE 'Misto' END AS assinatura,
      COUNT(*) n, ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (),1) pct
    FROM insc WHERE ano IN {ANOS_RECENTES} AND atendida=0 AND em_fila=0
    GROUP BY 1 ORDER BY n DESC
""")

run("3.3 — opcoes registradas na perda total, 2024-2025 combinado", f"""
    SELECT COUNT(*) n, ROUND(AVG(n_opcoes),2) media_opcoes,
      ROUND(100.0*SUM(CASE WHEN n_opcoes=1 THEN 1 ELSE 0 END)/COUNT(*),1) pct_uma_opcao
    FROM insc WHERE ano IN {ANOS_RECENTES} AND atendida=0 AND em_fila=0
""")

run("3.4 — % score valido>0 por assinatura, perda total 2024-2025 combinado", f"""
    WITH base AS (
      SELECT i.ano, i.prm_id, i.plm_id, i.ipl_id,
        CASE WHEN teve_cancel_sistema=1 AND teve_cancel_confirmacao=0 AND teve_cancel_simples=0 THEN 'So sistema'
             WHEN teve_cancel_sistema=0 AND teve_cancel_confirmacao=1 AND teve_cancel_simples=0 THEN 'So confirmacao'
             WHEN teve_cancel_sistema=0 AND teve_cancel_confirmacao=0 AND teve_cancel_simples=1 THEN 'So simples'
             ELSE 'Misto' END AS assinatura
      FROM insc i WHERE i.ano IN {ANOS_RECENTES} AND atendida=0 AND em_fila=0
    )
    SELECT b.assinatura, COUNT(*) n,
      ROUND(100.0*SUM(CASE WHEN s.score_valido>0 THEN 1 ELSE 0 END)/COUNT(*),1) pct_score_positivo
    FROM base b LEFT JOIN score s USING(ano,prm_id,plm_id,ipl_id)
    GROUP BY 1 ORDER BY n DESC
""")

run("3.5 — % score valido>0 por desfecho, 2024-2025 combinado", f"""
    SELECT
      CASE WHEN i.atendida=1 THEN 'Atendida' WHEN i.em_fila=1 THEN 'Fila' ELSE 'Cancelada' END desfecho,
      COUNT(*) n,
      ROUND(100.0*SUM(CASE WHEN s.score_valido>0 THEN 1 ELSE 0 END)/COUNT(*),1) pct_score_positivo
    FROM insc i JOIN score s USING(ano,prm_id,plm_id,ipl_id)
    WHERE i.ano IN {ANOS_RECENTES}
    GROUP BY 1 ORDER BY pct_score_positivo DESC
""")

print("\nFIM.")
