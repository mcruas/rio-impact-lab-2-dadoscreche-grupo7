from app.data import Escola
from app.distancia import EnderecoFamilia, centroides_por_bairro, distancia_mais_proxima, haversine_km


def test_haversine_zero_para_mesmo_ponto() -> None:
    assert haversine_km(-22.9, -43.2, -22.9, -43.2) == 0.0


def test_haversine_distancia_conhecida_rio_sao_paulo() -> None:
    # Distância aproximada Rio-SP em linha reta é ~360km.
    km = haversine_km(-22.9068, -43.1729, -23.5505, -46.6333)
    assert 340 < km < 380


def _escola(esc_codigo: str, bairro: str, lat: float | None, lon: float | None) -> Escola:
    return Escola(
        esc_codigo=esc_codigo,
        nome=f"Escola {esc_codigo}",
        endereco=None,
        bairro=bairro,
        latitude=lat,
        longitude=lon,
        tipo="Creche",
        indice_concorrencia=None,
    )


def test_centroides_por_bairro_ignora_escolas_sem_coordenada() -> None:
    escolas = [
        _escola("1", "Tijuca", -22.93, -43.23),
        _escola("2", "TIJUCA", -22.94, -43.24),
        _escola("3", "Tijuca", None, None),
    ]
    centroides = centroides_por_bairro(escolas)
    assert "TIJUCA" in centroides
    lat, lon = centroides["TIJUCA"]
    assert lat == (-22.93 + -22.94) / 2
    assert lon == (-43.23 + -43.24) / 2


def test_distancia_mais_proxima_escolhe_o_menor_entre_moradia_e_trabalho() -> None:
    centroides = {"MORADIA": (-22.90, -43.20), "TRABALHO": (-22.95, -43.25)}
    enderecos = [
        EnderecoFamilia(tipo="Moradia", bairro="moradia"),
        EnderecoFamilia(tipo="Trabalho", bairro="trabalho"),
    ]
    # escola bem perto do centróide de "trabalho"
    resultado = distancia_mais_proxima(enderecos, centroides, -22.951, -43.251)
    assert resultado is not None
    km, origem = resultado
    assert origem == "Trabalho"
    assert km < 1.0


def test_distancia_mais_proxima_none_sem_coordenada_da_escola() -> None:
    centroides = {"MORADIA": (-22.90, -43.20)}
    enderecos = [EnderecoFamilia(tipo="Moradia", bairro="moradia")]
    assert distancia_mais_proxima(enderecos, centroides, None, None) is None


def test_distancia_mais_proxima_none_sem_bairro_reconhecido() -> None:
    centroides = {"MORADIA": (-22.90, -43.20)}
    enderecos = [EnderecoFamilia(tipo="Moradia", bairro="bairro desconhecido")]
    assert distancia_mais_proxima(enderecos, centroides, -22.9, -43.2) is None
