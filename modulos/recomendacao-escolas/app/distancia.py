"""Distância entre endereços da família e escolas candidatas.

A posição da família é resolvida em dois níveis, do melhor para o pior:

1. **Pelo CEP**, quando o endereço traz um (`dados/ceps.csv`, ver `app/ceps.py`).
   Erro medido: mediana 0,65 km, p90 1,73 km.
2. **Pelo centróide do bairro** — lat/long médio das escolas cadastradas naquele
   bairro em `desafio/OferecimentosEvagas/Unidades_Unificadas_com_Localizacao.xlsx`,
   já carregado por `data.py`. É a aproximação antiga, mantida como fallback para
   pedidos sem CEP ou com CEP fora da tabela. Erro medido: mediana 0,97 km, p90 3,14 km.

Limitação que continua valendo: não geocodificamos o endereço exato (logradouro e
número) da família — isso exigiria um serviço externo de geocodificação, fora do escopo.
A precisão máxima aqui é a do CEP, não a da porta da casa. Documentar isso para quem for
calibrar a fórmula de pontuação depois.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .ceps import RegistroCep, normalizar_cep
from .data import Escola, _bairro_base, _normalizar


@dataclass(frozen=True)
class EnderecoFamilia:
    tipo: str  # "Moradia" ou "Trabalho"
    bairro: str
    cep: str | None = None
    """Quando presente e conhecido, dá uma posição bem melhor que o centróide do bairro."""


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    raio_terra_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return raio_terra_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def centroides_por_bairro(escolas: list[Escola]) -> dict[str, tuple[float, float]]:
    """bairro normalizado -> (lat médio, long médio) das escolas com coordenadas."""
    somas: dict[str, list[float]] = {}
    for escola in escolas:
        if escola.latitude is None or escola.longitude is None:
            continue
        chave = _normalizar(_bairro_base(escola.bairro))
        soma = somas.setdefault(chave, [0.0, 0.0, 0])
        soma[0] += escola.latitude
        soma[1] += escola.longitude
        soma[2] += 1
    return {
        chave: (lat_soma / n, lon_soma / n)
        for chave, (lat_soma, lon_soma, n) in somas.items()
        if n > 0
    }


def localizar_endereco(
    endereco: EnderecoFamilia,
    centroides: dict[str, tuple[float, float]],
    ceps: dict[str, RegistroCep] | None = None,
) -> tuple[float, float] | None:
    """Melhor coordenada disponível para um endereço da família: CEP, senão bairro."""
    if ceps:
        digitos = normalizar_cep(endereco.cep)
        registro = ceps.get(digitos) if digitos else None
        if registro is not None:
            return (registro.latitude, registro.longitude)
    return centroides.get(_normalizar(_bairro_base(endereco.bairro)))


def distancia_mais_proxima(
    enderecos: list[EnderecoFamilia],
    centroides: dict[str, tuple[float, float]],
    escola_lat: float | None,
    escola_lon: float | None,
    ceps: dict[str, RegistroCep] | None = None,
) -> tuple[float, str] | None:
    """Menor distância (km) da escola até qualquer um dos endereços da família.

    Retorna (distancia_km, tipo_do_endereco_mais_proximo), ou None se não houver
    coordenada suficiente (escola sem lat/long, ou nenhum endereço da família
    localizável nem por CEP nem por bairro).
    """
    if escola_lat is None or escola_lon is None:
        return None

    melhor: tuple[float, str] | None = None
    for endereco in enderecos:
        origem = localizar_endereco(endereco, centroides, ceps)
        if origem is None:
            continue
        km = haversine_km(origem[0], origem[1], escola_lat, escola_lon)
        if melhor is None or km < melhor[0]:
            melhor = (km, endereco.tipo)
    return melhor
