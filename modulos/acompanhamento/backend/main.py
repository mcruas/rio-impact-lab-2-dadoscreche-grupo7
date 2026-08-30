"""Stub do backend de Acompanhamento — contrato em contracts/acompanhamento.openapi.yaml.

TODO (quem implementar este módulo):
- GET /acompanhamento/{cpf}: chamar o Motor de Match (GET /status/{cpf}) só por HTTP
  e repassar o resultado (contracts/schemas/status_fila.schema.json).
"""

from fastapi import FastAPI

app = FastAPI(title="Acompanhamento", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
