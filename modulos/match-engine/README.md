# Motor de Match

> Módulo esqueleto — implementação a fazer. Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema e [`../recomendacao-escolas/`](../recomendacao-escolas/)
> como referência de estrutura/qualidade.

## Responsabilidade

Define os **critérios de match** (pontuação socioeconômica/de vulnerabilidade) e
calcula, para cada inscrição, a posição na fila / desfecho. Contrato público:
[`../../contracts/match-engine.openapi.yaml`](../../contracts/match-engine.openapi.yaml).

## O que este módulo consome

- [`inscricao.openapi.yaml`](../../contracts/inscricao.openapi.yaml) (`GET /inscricoes/{cpf}`)
- [`documentacao.openapi.yaml`](../../contracts/documentacao.openapi.yaml) (`GET /documentos?inscricao_id=`)

**Só por contrato** — nunca acessar o banco/código interno desses módulos diretamente.

## O que este módulo expõe

- `GET /criterios` — lista os critérios de match vigentes e seus pesos.
- `GET /status/{cpf}` — consultado pelo módulo `acompanhamento/` (Tela 3) para mostrar
  a posição na fila.

## Cuidado ao desenhar os critérios (lições da EDA do próprio desafio)

Antes de montar a régua de pontuação, ler [`../../eda/RESULTADOS_H6_H12.md`](../../eda/RESULTADOS_H6_H12.md) —
os mesmos dados anonimizados desta pasta já foram analisados e revelaram armadilhas
de modelagem reais que valem para qualquer motor de pontuação parecido:

- **Um critério "atendido" só deve contar ponto quando a resposta E a validação
  concordam** (no dado original: `resposta='Sim' AND confirmado='Sim'`) — usar só a
  validação sozinha infla a pontuação, porque ela também ocorre em respostas negativas
  validadas.
- **Pontuação bruta não é comparável entre regras diferentes** (o desafio documentou
  uma reforma que mudou pesos de forma não-linear entre anos) — se este motor também
  evoluir os pesos com o tempo, versionar o conjunto de critérios (`criterio_id`) e
  nunca comparar pontuação de duas versões diferentes diretamente.
- Distribuições de pontuação tendem a ser concentradas em poucos valores (muitas
  inscrições com pontuação zero) — cuidado com médias; prefira métricas robustas
  (ex.: % acima de um limiar) ao decidir se a régua está discriminando bem.

## Como começar

```bash
cd modulos/match-engine/backend
python -m venv .venv && source .venv/Scripts/activate
pip install fastapi "uvicorn[standard]" pydantic
uvicorn main:app --reload
```
