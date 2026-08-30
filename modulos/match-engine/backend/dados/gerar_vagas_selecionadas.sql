-- Gera dados/vagas_selecionadas.csv a partir da Query A bruta do desafio
-- (desafio/Bases IC_ ClassificadoseFila/01_QueryA_InscricoesPorAno.csv.gz,
-- nao versionada -- ver .gitignore). Rodar com `duckdb -c "$(cat gerar_vagas_selecionadas.sql)"`
-- depois de ajustar o caminho abaixo para onde a Query A bruta estiver.
--
-- Ao contrario de match_opcoes.csv (sem pipeline de geracao documentado em
-- nenhum lugar do repositorio), este arquivo e pequeno o bastante (159
-- linhas) para regenerar do zero sempre que precisar -- nao precisa entrar
-- no pipeline principal do motor de match.

COPY (
    SELECT aluno_anon, opcao, unidade, situacao, min(data_criacao) AS data_criacao
    FROM read_csv_auto('desafio/Bases IC_ ClassificadoseFila/01_QueryA_InscricoesPorAno.csv.gz', delim=';')
    WHERE ano = 2025 AND situacao IN ('Selecionado', 'Selecionado da lista')
    GROUP BY aluno_anon, opcao, unidade, situacao
    ORDER BY aluno_anon, opcao
) TO 'vagas_selecionadas.csv' (HEADER, DELIMITER ',');
