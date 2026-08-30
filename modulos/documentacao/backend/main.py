"""Stub do backend de Documentação — contrato em contracts/documentacao.openapi.yaml.

TODO (quem implementar este módulo):
- POST /documentos: validar contra contracts/schemas/documento.schema.json e persistir.
- GET /documentos?inscricao_id=: listar documentos de uma inscrição.
- Chamar o backend de Inscrição (GET /inscricoes/{cpf}) só por HTTP, para confirmar
  que a inscrição existe antes de aceitar documentos.
"""

from fastapi import FastAPI

app = FastAPI(title="Documentação", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
