"""Resolução de CEP -> bairro.

Duas fontes, nesta ordem:

1. `dados/ceps.csv` (ver `app/ceps.py`) — tabela local, precomputada a partir das
   inscrições reais da Query A e commitada no git. Resolve ~20,8 mil CEPs sem rede,
   sem latência e sem ponto de falha externo. É o caminho normal.
2. ViaCEP (viacep.com.br), API pública brasileira, gratuita e sem autenticação —
   só para CEPs que não estão na tabela (ex.: CEP novo, ou de fora do município).

A chamada externa fica no backend, nunca no frontend, para manter o frontend sem
conhecimento de serviços externos — consistente com a regra de contratos da
arquitetura (ver ../../ARQUITETURA.md). No fallback vale o de sempre: timeout curto e
qualquer erro (rede, CEP inexistente, resposta malformada) vira None, nunca derruba a
request de quem chamou.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from .ceps import normalizar_cep, tabela_ceps

VIACEP_TIMEOUT_SEGUNDOS = 4.0


@dataclass(frozen=True)
class LocalizacaoCep:
    bairro: str
    latitude: float | None
    longitude: float | None
    """None quando o CEP só existe no ViaCEP — a API não devolve coordenada. Quem
    consome precisa aguentar isso (ex.: não plotar o pino da família no mapa)."""


def resolver_cep(cep: str) -> LocalizacaoCep | None:
    """Bairro + coordenada de um CEP. None se o CEP não existe em lugar nenhum."""
    digitos = normalizar_cep(cep)
    if digitos is None:
        return None

    registro = tabela_ceps().get(digitos)
    if registro is not None and registro.bairro:
        return LocalizacaoCep(
            bairro=registro.bairro,
            latitude=registro.latitude,
            longitude=registro.longitude,
        )

    bairro = _consultar_viacep(digitos)
    return None if bairro is None else LocalizacaoCep(bairro=bairro, latitude=None, longitude=None)


def resolver_bairro_por_cep(cep: str) -> str | None:
    localizacao = resolver_cep(cep)
    return None if localizacao is None else localizacao.bairro


def _consultar_viacep(digitos: str) -> str | None:
    """Fallback de rede, só para CEP fora de dados/ceps.csv."""
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
