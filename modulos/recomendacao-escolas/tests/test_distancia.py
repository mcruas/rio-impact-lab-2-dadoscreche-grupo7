from app.ceps import RegistroCep
from app.data import Escola
from app.distancia import (
    EnderecoFamilia,
    centroides_por_bairro,
    distancia_mais_proxima,
    haversine_km,
    localizar_endereco,
)


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


def _cep(cep: str, lat: float, lon: float) -> RegistroCep:
    return RegistroCep(
        cep=cep,
        bairro="Tijuca",
        latitude=lat,
        longitude=lon,
        origem_coord="cep_exato",
        cod_territ=None,
        cre=None,
        n_inscricoes=1,
    )


def test_localizar_endereco_prefere_o_cep_ao_centroide_do_bairro() -> None:
    centroides = {"TIJUCA": (-22.93, -43.23)}
    ceps = {"20511170": _cep("20511170", -22.92, -43.24)}
    endereco = EnderecoFamilia(tipo="Moradia", bairro="Tijuca", cep="20511170")
    assert localizar_endereco(endereco, centroides, ceps) == (-22.92, -43.24)


def test_localizar_endereco_cai_no_bairro_sem_cep_ou_com_cep_desconhecido() -> None:
    centroides = {"TIJUCA": (-22.93, -43.23)}
    ceps = {"20511170": _cep("20511170", -22.92, -43.24)}
    sem_cep = EnderecoFamilia(tipo="Moradia", bairro="Tijuca")
    fora_da_tabela = EnderecoFamilia(tipo="Moradia", bairro="Tijuca", cep="99999999")
    assert localizar_endereco(sem_cep, centroides, ceps) == (-22.93, -43.23)
    assert localizar_endereco(fora_da_tabela, centroides, ceps) == (-22.93, -43.23)


def test_localizar_endereco_aceita_cep_com_hifen() -> None:
    ceps = {"20511170": _cep("20511170", -22.92, -43.24)}
    endereco = EnderecoFamilia(tipo="Moradia", bairro="Tijuca", cep="20511-170")
    assert localizar_endereco(endereco, {}, ceps) == (-22.92, -43.24)


def test_distancia_mais_proxima_usa_o_cep_quando_disponivel() -> None:
    # A escola fica exatamente em cima do CEP e longe do centróide do bairro:
    # com CEP a distância tem de ser ~0, sem CEP tem de ser bem maior.
    centroides = {"TIJUCA": (-22.99, -43.30)}
    ceps = {"20511170": _cep("20511170", -22.92, -43.24)}
    com_cep = [EnderecoFamilia(tipo="Moradia", bairro="Tijuca", cep="20511170")]
    sem_cep = [EnderecoFamilia(tipo="Moradia", bairro="Tijuca")]

    km_com, _ = distancia_mais_proxima(com_cep, centroides, -22.92, -43.24, ceps)
    km_sem, _ = distancia_mais_proxima(sem_cep, centroides, -22.92, -43.24, ceps)
    assert km_com == 0.0
    assert km_sem > 5


def test_distancia_mais_proxima_sem_tabela_de_ceps_mantem_o_comportamento_antigo() -> None:
    centroides = {"TIJUCA": (-22.93, -43.23)}
    enderecos = [EnderecoFamilia(tipo="Moradia", bairro="Tijuca", cep="20511170")]
    assert distancia_mais_proxima(enderecos, centroides, -22.93, -43.23) == (0.0, "Moradia")
