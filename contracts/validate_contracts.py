"""Valida que os contratos em contracts/ sao bem formados.

Uso: python contracts/validate_contracts.py (a partir da raiz do repo, ou de
dentro de contracts/ - o script resolve os caminhos relativos a este arquivo).

Nao valida a implementacao de nenhum modulo, so a forma dos contratos:
- schemas/*.schema.json: JSON Schema valido (draft 2020-12).
- *.openapi.yaml: documento OpenAPI 3.x valido, incluindo os $ref para os schemas.
"""

import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from openapi_spec_validator import validate as validate_openapi
from openapi_spec_validator.readers import read_from_filename

BASE_DIR = Path(__file__).resolve().parent


def validar_schemas() -> list[str]:
    erros = []
    for path in sorted((BASE_DIR / "schemas").glob("*.schema.json")):
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except Exception as exc:  # noqa: BLE001 - queremos reportar qualquer erro
            erros.append(f"{path.name}: {exc}")
    return erros


def validar_openapi() -> list[str]:
    erros = []
    for path in sorted(BASE_DIR.glob("*.openapi.yaml")):
        try:
            spec, base_uri = read_from_filename(str(path))
            validate_openapi(spec, base_uri=base_uri)
        except Exception as exc:  # noqa: BLE001
            erros.append(f"{path.name}: {exc}")
    return erros


def main() -> int:
    erros = validar_schemas() + validar_openapi()
    total_arquivos = len(list((BASE_DIR / "schemas").glob("*.schema.json"))) + len(
        list(BASE_DIR.glob("*.openapi.yaml"))
    )
    if erros:
        print(f"FALHOU: {len(erros)} de {total_arquivos} contrato(s) com problema:\n")
        for erro in erros:
            print(f"  - {erro}")
        return 1
    print(f"OK: {total_arquivos} contrato(s) validado(s) com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
