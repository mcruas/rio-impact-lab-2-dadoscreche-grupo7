"""Stub do backend de Inscrição — contrato em contracts/inscricao.openapi.yaml.

TODO (quem implementar este módulo):
- POST /inscricoes: validar contra contracts/schemas/inscricao.schema.json e persistir.
- GET /inscricoes/{cpf}: buscar por CPF da criança OU do responsável.
- Chamar o backend de Recomendação de Escola (GET /escolas?bairro=) só por HTTP,
  nunca importando código dele diretamente.
"""

from fastapi import FastAPI

app = FastAPI(title="Inscrição", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
