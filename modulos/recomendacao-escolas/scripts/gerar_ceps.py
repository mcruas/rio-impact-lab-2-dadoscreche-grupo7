"""Gera dados/ceps.csv e dados/cep_escolas.csv a partir de desafio/.

Rodar a partir de modulos/recomendacao-escolas/, com desafio/ presente e
dados/escolas.duckdb já gerado (rodar scripts/gerar_dataset.py antes):
    python scripts/gerar_ceps.py

Os arquivos gerados são commitados no git e são o que o app lê em runtime
(app/ceps.py::carregar_ceps / carregar_cep_escolas) — sem eles, `GET /cep/{cep}`
volta a depender do ViaCEP pela rede e a distância volta a ser aproximada pelo
centróide de bairro. Ver o cabeçalho de app/ceps.py para a cascata de resolução
de coordenada e os números de cobertura.

Regenerar sempre que os dados de desafio/ mudarem (ex.: nova exportação da Query A
ou de Unidades_Unificadas_com_Localizacao.xlsx).
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ceps import (  # noqa: E402
    CEP_ESCOLAS_CSV,
    CEPS_CSV,
    recalcular_de_desafio,
)


def main() -> None:
    registros, vizinhas = recalcular_de_desafio()

    CEPS_CSV.parent.mkdir(parents=True, exist_ok=True)

    with CEPS_CSV.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(
            [
                "cep",
                "bairro",
                "latitude",
                "longitude",
                "origem_coord",
                "cod_territ",
                "cre",
                "n_inscricoes",
            ]
        )
        for r in registros:
            escritor.writerow(
                [
                    r.cep,
                    r.bairro,
                    f"{r.latitude:.6f}",
                    f"{r.longitude:.6f}",
                    r.origem_coord,
                    r.cod_territ or "",
                    "" if r.cre is None else r.cre,
                    r.n_inscricoes,
                ]
            )

    with CEP_ESCOLAS_CSV.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["cep", "ordem", "esc_codigo", "distancia_km", "mesma_microarea"])
        for cep, v in vizinhas:
            escritor.writerow(
                [cep, v.ordem, v.esc_codigo, f"{v.distancia_km:.3f}", str(v.mesma_microarea).lower()]
            )

    # Resumo: quanto da demanda real cada nível da cascata resolveu.
    total_inscricoes = sum(r.n_inscricoes for r in registros)
    por_origem = Counter()
    for r in registros:
        por_origem[r.origem_coord] += r.n_inscricoes

    print(f"OK: {len(registros)} CEPs gravados em {CEPS_CSV}")
    print(f"OK: {len(vizinhas)} pares CEP-escola gravados em {CEP_ESCOLAS_CSV}")
    print("\nCobertura por origem da coordenada (% das inscrições):")
    acumulado = 0.0
    for origem in ("cep_exato", "prefixo5", "prefixo3", "bairro"):
        pct = 100.0 * por_origem[origem] / total_inscricoes
        acumulado += pct
        print(f"  {origem:10} {pct:5.1f}%   (acumulado {acumulado:5.1f}%)")

    sem_microarea = sum(1 for r in registros if r.cod_territ is None)
    print(f"\nCEPs sem microárea (fora dos polígonos SME): {sem_microarea}")


if __name__ == "__main__":
    main()
