"""Resolução de CEP -> bairro via ViaCEP (viacep.com.br), API pública brasileira,
gratuita e sem autenticação. Chamada só pelo backend (nunca pelo frontend
diretamente) para manter o frontend sem conhecimento de serviços externos —
consistente com a regra de contratos da arquitetura (ver ../../ARQUITETURA.md).

Isso introduz uma dependência de rede em tempo de request: timeout curto e
qualquer erro (rede, CEP inexistente, resposta malformada) vira None, nunca
derruba a request de quem chamou.
"""

from __future__ import annotations

import httpx

VIACEP_TIMEOUT_SEGUNDOS = 4.0


def resolver_bairro_por_cep(cep: str) -> str | None:
    digitos = "".join(c for c in cep if c.isdigit())
    if len(digitos) != 8:
        return None

    try:
        resp = httpx.get(
            f"https://viacep.com.br/ws/{digitos}/json/",
            timeout=VIACEP_TIMEOUT_SEGUNDOS,
        )
        resp.raise_for_status()
        dados = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    if dados.get("erro"):
        return None

    bairro = dados.get("bairro")
    return bairro.strip() if bairro else None
