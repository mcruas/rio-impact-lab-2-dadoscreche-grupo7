"""Entrypoint da função serverless Python do Vercel.

O runtime do Vercel (@vercel/python) detecta a variável `app` (ASGI) neste
arquivo e a expõe como a função — ver vercel.json (raiz deste módulo).
Reexporta o mesmo FastAPI de app/main.py, sem duplicar nada.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

__all__ = ["app"]
