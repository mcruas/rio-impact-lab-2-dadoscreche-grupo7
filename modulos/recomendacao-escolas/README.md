# Recomendação de Escola

Backend consumido pela Tela 1 (Inscrição): dado onde a família mora (e opcionalmente
onde trabalha), recomenda e **explica** as melhores escolas — combinando proximidade,
o quão concorrida cada escola costuma ser, o score estimado da família e o histórico
de não-comparecimento do responsável. Contrato público em
[`../../contracts/recomendacao-escolas.openapi.yaml`](../../contracts/recomendacao-escolas.openapi.yaml).

Este é o **módulo de referência** da arquitetura (ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)):
totalmente implementado, para servir de modelo de estrutura/qualidade para os demais.

## Endpoints

- `GET /cep/{cep}` — resolve um CEP pra bairro pela **tabela local `dados/ceps.csv`**
  (`app/ceps.py`), sem rede. Só cai no **ViaCEP** (`app/cep.py`, API pública brasileira,
  gratuita, sem autenticação) para CEP que não esteja na tabela. Usado pelo frontend
  antes de chamar `/recomendacoes` quando a família digita CEP em vez de bairro.
- `GET /escolas?bairro=` — listagem simples, sem ranking (ex.: para popular um mapa
  com "tudo da região"). Mantido do módulo original.
- `POST /recomendacoes` — o recomendador de verdade. Recebe endereço(s) da família,
  e opcionalmente `score_estimado` (percentil) e `historico_responsavel`, devolve as
  escolas mais bem pontuadas com o racional (`rationale`) de cada uma.
- `GET`/`POST /admin/recomendacoes` — página HTML simples pra testar/auditar o
  recomendador no navegador sem precisar de nenhum frontend pronto. O `POST` chama a
  **mesma função interna** (`_rankear`, em `app/main.py`) usada pela API real — a
  explicação mostrada é fiel ao que o sistema de fato calculou, não uma reimplementação
  paralela.

CORS liberado (`CORSMiddleware`, origem configurável via env `CORS_ORIGINS`, default
`*`) — necessário pro frontend chamar a API direto do navegador.

## Como o ranking funciona (`app/pontuacao.py`)

Três sinais, cada um 0-100 (histórico só penaliza), somados com pesos fixos e
documentados — **nada de modelo caixa-preta**, para toda sugestão poder ser explicada:

```
pontuacao_final = 0.5 * pontos_proximidade + 0.3 * pontos_adequacao_score + 0.2 * pontos_historico
```

- **`pontos_proximidade`** (peso dominante): decai linearmente de 100 (distância ~0km)
  a 0 (10km ou mais). Distância = a menor entre (moradia→escola) e (trabalho→escola).
- **`pontos_adequacao_score`**: casa o **percentil do score estimado** da família com o
  **índice de concorrência** histórico da escola (`app/data.py`, calculado a partir de
  Query A: `1 - taxa de inscrições atendidas nessa unidade`). Score alto + escola muito
  concorrida = pontuação alta (é um "risco" compatível com o perfil); score baixo +
  escola muito concorrida = pontuação baixa. Usa **percentil**, não valor bruto, porque
  a régua de pontuação muda entre anos/versões (ver `eda/RESULTADOS_H6_H12.md`) —
  comparar percentil-a-percentil é robusto a isso. Sem score ou sem índice de
  concorrência, o valor é neutro (nem ajuda nem atrapalha).
- **`pontos_historico`**: penalidade proporcional à taxa de não-comparecimento do
  responsável **e** ao índice de concorrência da escola — só penaliza forte em escolas
  concorridas (não faz sentido penalizar em escolas sem disputa). Zero sem histórico.

A `escola_preferida_esc_codigo`, se informada, sempre aparece na resposta (com a
pontuação real, mesmo que baixa) — o objetivo é dar feedback honesto pra família, não
esconder que a preferida está fora de alcance.

## Microárea SME (`app/microarea.py`)

Cada escola devolvida por `GET /escolas` e `POST /recomendacoes` vem marcada com
`cod_territ`/`cre` — a microárea (233 polígonos) e CRE (11 coordenadorias) do
shapefile `desafio/Microáreas_SME_revisãoIPP/` que contêm a coordenada da escola,
via ponto-em-polígono com a extensão `spatial` do DuckDB (sem lib nova, mesmo
padrão do `read_xlsx` já usado em `app/data.py`).

Isso é hoje só metadado de explicabilidade/agrupamento — o ranking continua
usando distância real em km (`pontos_proximidade` acima), porque o tamanho das
microáreas varia demais (mediana 2,5 km², de 0,12 km² no centro a 78,6 km² na
Zona Oeste) pra tratar "mesma microárea" como filtro binário de recomendação; em
áreas grandes isso esconderia diferenças de vários km entre escolas "da mesma
região". Também não dá pra derivar microárea a partir do nome do bairro: o
shapefile não tem esse campo, e um único bairro chega a cobrir 7-9 microáreas
diferentes (ex.: escolas do bairro Tijuca já saem marcadas com `cod_territ`
`2.11`, `2.13` e `2.15` — três microáreas distintas).

**Limitação atual**: só a escola tem coordenada. A família só informa `bairro`
em `endereco.schema.json` (sem lat/long), então ainda não dá pra atribuir
microárea ao lado da família — falta um endereço geocodificado ou a
geolocalização do dispositivo chegando no pedido, o que exigiria estender
`endereco.schema.json` (mudança que precisa de acordo com quem implementa
`inscricao`, que também usa esse schema).

**Pegadinha real (custou tempo de debug)**: o `ST_Transform` do DuckDB espera por
padrão eixo (latitude, longitude) para EPSG:4326 — passar `ST_Point(longitude,
latitude)` sem `always_xy := true` transforma o ponto silenciosamente (sem erro
nenhum) para uma posição a centenas de km de distância. Sempre usar
`always_xy := true`.

## Limitações conhecidas (documentadas no código)

- **Proximidade é aproximada por CEP, não por endereço exato** (`app/distancia.py`):
  sem um serviço de geocodificação não dá para chegar no número da porta. Quando o
  pedido traz `cep`, a posição da família vem de `dados/ceps.csv` (erro mediano
  0,65 km); sem `cep`, cai no centróide das escolas do bairro (erro mediano 0,97 km).
  Suficiente para ranking, não para navegação.
- **`indice_concorrencia`** é uma heurística sobre dados anonimizados (ver `CLAUDE.md`)
  — ilustra a dinâmica, não é uma métrica oficial.
- **Uma escola vem com coordenada zerada** em `Unidades_Unificadas_com_Localizacao.xlsx`:
  a Escola Municipal Pedro Bruno (`esc_codigo` 121002, Paquetá) tem `LATITUDE`/`LONGITUDE`
  = 0. Como `0` não é nulo, ela contaminava o centróide de Paquetá, que ia parar em
  (-11,38, -21,55) — a média entre a ilha e a "null island" — e toda família de Paquetá
  recebia distância sem sentido. `app/data.py::_coordenada()` passou a tratar `(0, 0)`
  como coordenada ausente; a unidade fica de fora do ranking por distância, como
  qualquer outra sem lat/long.
- **`BAIRRO` em `Unidades_Unificadas_com_Localizacao.xlsx` tem ~323 valores distintos**
  para bem menos bairros reais (mesma unidade com bairro em MAIÚSCULO e Title Case,
  sufixos tipo "Andaraí - Jamelão"). A busca normaliza (sem acento, maiúsculo, corta
  sufixo após " - "/" (") — mas variantes sem esse padrão (ex.: "Alto da Boa Vista" vs
  "Alto Boa Vista") continuam sendo bairros diferentes.
- Não depende de nenhum outro módulo de `modulos/` em runtime — `score_estimado` e
  `historico_responsavel` chegam prontos no corpo do pedido (ver
  [`../../contracts/README.md`](../../contracts/README.md)); quem deve buscá-los no
  `match-engine` antes de chamar este módulo é o `inscricao/`.

## Dataset pré-processado (`dados/escolas.duckdb`)

`app/data.py::carregar_escolas()` **não lê `desafio/` em produção** — lê
`dados/escolas.duckdb`, um arquivo pequeno (~1941 linhas, poucas centenas de KB)
já com o join completo (Query A + microárea) feito, gerado por
`scripts/gerar_dataset.py` e **commitado no git**. Isso é o que permite rodar em
deploy (Vercel etc.) sem precisar de `desafio/` nem das extensões `excel`/`spatial`
do DuckDB em runtime.

Regenerar sempre que os dados de `desafio/` mudarem (precisa de `desafio/`
presente localmente):

```bash
python scripts/gerar_dataset.py
```

A lógica completa (ler `desafio/`, cruzar com Query A e o shapefile de microárea)
continua em `recalcular_de_desafio()`, só que agora é chamada só por esse script,
não a cada request.

## Tabela por CEP (`dados/ceps.csv` e `dados/cep_escolas.csv`)

Mesma ideia do dataset acima, agora para o lado da família: onde fica cada CEP e quais
escolas ficam perto dele são fatos estáveis, não coisa de recalcular por request.
Gerados por `scripts/gerar_ceps.py` (precisa de `desafio/` **e** de
`dados/escolas.duckdb` já gerado) e lidos por `app/ceps.py`:

| Arquivo | Linhas | Colunas |
| --- | --- | --- |
| `dados/ceps.csv` | ~20,8 mil | `cep, bairro, latitude, longitude, origem_coord, cod_territ, cre, n_inscricoes` |
| `dados/cep_escolas.csv` | ~208 mil | `cep, ordem, esc_codigo, distancia_km, mesma_microarea` |

As coordenadas saem **só de dados locais, sem nenhuma API de geocodificação**: a Query D
(`04_UnidadesEscolaresComEndereco.csv`) tem o CEP de cada escola e o catálogo tem a
lat/long dela, o que dá ~1.900 âncoras "CEP real → coordenada real". Como o CEP
brasileiro é hierárquico, essas âncoras resolvem o resto por prefixo:

| `origem_coord` | regra | % das inscrições (acumulado) |
| --- | --- | --- |
| `cep_exato` | CEP igual ao de alguma escola | 23,8% |
| `prefixo5` | centróide das âncoras do prefixo de 5 dígitos | 97,7% |
| `prefixo3` | centróide das âncoras do prefixo de 3 dígitos | 99,8% |
| `bairro` | centróide das escolas do bairro | 100% |

A coluna `origem_coord` fica gravada por CEP justamente para dar para auditar e filtrar
por precisão depois.

```bash
python scripts/gerar_ceps.py
```

A BrasilAPI foi testada como fonte de coordenada e **descartada**: numa amostra de 120
CEPs, 77% devolveram a mesma sentinela `-22.90642,-43.18223` (centro do Rio) em vez da
coordenada real — Copacabana, Ramos, Inhaúma e Camorim vinham todos no mesmo ponto.

## Rodar localmente

```bash
cd modulos/recomendacao-escolas
python -m venv .venv
source .venv/Scripts/activate   # Windows Git Bash; no PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Testar:

```bash
curl "http://127.0.0.1:8000/cep/23050-300"
curl "http://127.0.0.1:8000/escolas?bairro=Tijuca"

curl -X POST http://127.0.0.1:8000/recomendacoes -H "Content-Type: application/json" \
  -d '{"enderecos":[{"tipo":"Moradia","bairro":"Tijuca"}],"score_estimado":{"percentil":0.9}}'

# Com `cep`, a distância sai bem mais precisa (compare com o de cima):
curl -X POST http://127.0.0.1:8000/recomendacoes -H "Content-Type: application/json" \
  -d '{"enderecos":[{"tipo":"Moradia","bairro":"Tijuca","cep":"20511170"}]}'
```

Ou abra `http://127.0.0.1:8000/admin/recomendacoes` no navegador para o formulário.

## Testes

```bash
pytest tests               # tudo
pytest tests -m "not rede" # só o que roda offline (o normal)
```

Só os dois testes marcados com `@pytest.mark.rede` em `tests/test_cep.py` precisam de
internet — cobrem o fallback do ViaCEP para CEP fora da tabela. Todo o resto, inclusive
o caminho normal de `GET /cep/{cep}`, roda offline.

## Deploy no Vercel

`api/index.py` reexporta o mesmo `app` de `app/main.py`; `vercel.json` roteia
tudo pra essa função (padrão de função Python serverless do Vercel). Ao criar o
projeto no Vercel, aponte o **Root Directory** para `modulos/recomendacao-escolas`.
`requirements.txt` é instalado automaticamente pelo builder `@vercel/python`.
Não precisa de `desafio/` nem variável de ambiente nenhuma além de, opcionalmente,
`CORS_ORIGINS` (domínio do frontend, se quiser restringir além do `*` padrão).
