"""Stub do Motor de Match — contrato em contracts/match-engine.openapi.yaml.

TODO (quem implementar este módulo):
- GET /criterios: expor os critérios de match vigentes (contracts/schemas/criterio_match.schema.json).
- GET /status/{cpf}: calcular/consultar a posição na fila (contracts/schemas/status_fila.schema.json).
- Antes de desenhar a régua de pontuação, ler ../README.md (seção "Cuidado ao
  desenhar os critérios") e eda/RESULTADOS_H6_H12.md.
- Consumir Inscrição e Documentação só por HTTP (contratos), nunca por import direto.
"""

from fastapi import FastAPI

app = FastAPI(title="Motor de Match", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
