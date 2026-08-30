# Motor de Match

> Implementado. Especificação, algoritmo e backtest completos em
> [`MATCHING.md`](MATCHING.md). Ver [`../../ARQUITETURA.md`](../../ARQUITETURA.md)
> para a visão geral do sistema.

## Responsabilidade

Define os **critérios de match** (pontuação socioeconômica/de vulnerabilidade) e
calcula, para cada inscrição, a posição na fila / desfecho. Contrato público:
[`../../contracts/match-engine.openapi.yaml`](../../contracts/match-engine.openapi.yaml).

O motor em si (`backend/motor.py`) é aceitação diferida (Gale-Shapley) com reserva
territorial mole — ver [`MATCHING.md`](MATCHING.md) para o algoritmo completo e o
backtest sobre os dados reais de 2025. `backend/main.py` só liga esse motor ao
contrato REST abaixo.

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

## Limitações conhecidas do contrato face aos dados reais

Descobertas ao ligar o motor ao contrato — cada uma é uma decisão deliberada, não
uma omissão:

- **`{cpf}` recebe, na prática, o código `aluno_anon`.** A base do desafio é
  anonimizada e não tem CPF real (ver P5 em `PROBLEMAS.md`, e a nota "Precisamos de
  CPF" em `../../INTEGRACAO_RMI_WHATSAPP.md`). O contrato continua com o nome `cpf`
  por não exigir mudança combinada com quem consome; o vínculo com CPF de verdade
  só existe em produção, via RMI.
- **`status` só usa 2 dos 4 valores do enum** (`Confirmado` / `ListaDeEspera`). O
  motor roda uma rodada até convergir e não modela estado intermediário
  (`EmFila`) nem desistência/cancelamento (`Cancelado`) — não é omissão, é o que o
  algoritmo de fato produz.
- **`posicao_fila` é a posição na ordem de mérito GLOBAL** (pontuação → desempates
  → sorteio), não a posição numa fila por unidade — o motor processa uma ordem
  única para todas as escolas, não mantém fila por escola. `null` quando a criança
  já está `Confirmado`.
- **`escola_alocada` guarda só o `esc_codigo` (unidade)**, nunca grupamento/turno —
  o schema não tem campo para isso (`additionalProperties: false`). Checado nos
  dados reais: **24 de 62.891 famílias (0,04%)** têm opções em mais de um
  grupamento, então essa é uma perda real, mas rara.

## Como começar

```bash
cd modulos/match-engine/backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
