# Implementação do motor de matching

Especificação e resultado do backtest do algoritmo de alocação para o Eixo 2.
Código de referência em `motor/matching.py`, dados em `motor/dados/`,
validado sobre os dados reais de 2025 (62.891 crianças, 2.114 estratos
unidade×grupamento×turno).

> Ver também [`eda/RESULTADOS_MATCHING.md`](eda/RESULTADOS_MATCHING.md) para como estes achados se cruzam com a EDA do grupo (H1-H16, `eda/HIPOTESES_EDA.md` e `eda/RESULTADOS_H6_H12.md`).

## Algoritmo

Todas as unidades ordenam as crianças pela **mesma régua legal** — nenhuma
creche tem critério próprio de prioridade. Isso permite simplificar bastante
a implementação, mas só **sem reserva**: com prioridade comum e sem assentos
de tipo especial, aceitação diferida colapsa numa única ordem global
processada uma vez (cada criança pega a melhor opção ainda livre). A reserva
territorial quebra essa simplificação — os assentos reservados têm uma
prioridade diferente dos abertos — então o motor roda **aceitação diferida
de verdade**, uma rodada só, com cada estrato tratando seus assentos em duas
prioridades:

```
ordem_global = ordenar todas as criancas por
  (pontuacao legal desc, irmao na rede, pais/responsaveis <18, sorteio unico)

Cada estrato (unidade x grupamento x turno) tem:
  assentos ABERTOS     (65% da capacidade) -- prioridade = ordem_global
  assentos RESERVADOS  (35% da capacidade) -- prioridade = local > nao-local,
                                               e dentro de cada grupo, ordem_global

RODADA (repete ate ninguem mais propor):
  cada crianca livre propoe a sua proxima opcao ainda nao tentada
  cada estrato recebe as propostas + quem ja estava retido, e RETEM os
    melhores ate a capacidade total: primeiro preenche os assentos abertos
    pela ordem global, depois os reservados (locais primeiro; se nao houver
    local suficiente, nao-locais preenchem o resto -- reserva MOLE, nunca
    fica vaga reservada ociosa havendo qualquer criança elegível esperando)
  quem foi rejeitado (novo ou destituido por alguem melhor) volta a propor
```

Rodar assentos **abertos antes de reservados** evita gastar a reserva
territorial em crianças que entrariam por mérito de qualquer jeito — o
oposto desperdiça a reserva exatamente nas crianças de maior pontuação, que
não precisavam dela.

**Desempate:** dois critérios legais antes do sorteio — possui irmão
matriculado na rede pública ou parceria, e pais/responsáveis com idade menor
que 18 anos (`Query C`, `perg_criterio='Sim'`, estáveis nos 5 anos da base,
valem 0 pontos mas são critério de prioridade). Só depois vem o sorteio:
único por criança (`hash(semente pública + código da criança)`, nunca
reaproveitada entre processos), documentado e auditável — não a data de
inscrição, que é o desempate hoje e não tem respaldo legal nenhum.

**Desempenho medido:** roda em menos de 2s em Python puro para as 62.891
crianças, sem biblioteca externa. Não é o gargalo do sistema.

## Dois bugs encontrados e corrigidos antes de qualquer entrega

A primeira versão deste motor usava três passes sequenciais (abertas →
reservadas → sobra) em vez de aceitação diferida de verdade, e a capacidade
por estrato vinha de uma leitura com bug. Uma revisão independente do
desenho encontrou os dois problemas; verifiquei os dois rodando código antes
de aceitar qualquer conclusão.

**1. Os três passes não eram à prova de estratégia.** Passes sequenciais são
irreversíveis: uma criança alocada numa opção pior no passe 1 nunca era
reconsiderada para uma vaga reservada melhor no passe 2, mesmo sendo do
território e elegível. Contraexemplo mínimo que rodei no código antigo:

```
i mora no bairro de A, prefere A > B.  j tem mais pontos e quer A.
  i lista A e B (sincera)  ->  i vai para B    (a reservada de A fica VAZIA)
  i lista só A (trunca)    ->  i vai para A
```

Truncar a lista melhorava o resultado — o oposto exato da mensagem do P1
("liste mais opções, nunca prejudica"). Corrigido trocando os três passes
por uma rodada de aceitação diferida com prioridade específica por assento
(descrita acima). No mesmo contraexemplo, o motor corrigido aloca `i` em A
nos dois cenários — mentir deixou de compensar.

**2. A capacidade estava subestimada em 531 vagas.** O carregamento gravava
a situação real da criança por estrato com sobrescrita simples
(`dict[chave] = valor`); quando a mesma criança tinha mais de uma linha para
o mesmo estrato — 2.421 pares (criança, estrato) no CSV, 1.401 com situação
divergente entre as linhas —, a última lida vencia, mesmo quando era
`Cancelado pelo sistema` sobrescrevendo um `Confirmado` real. Isso subestimou
o número real de confirmadas em 2025: **48.144 → 48.675** depois de corrigir
para manter a **melhor** situação por estrato (`Confirmado` > `Selecionado` >
`Lista de espera` > `Cancelado...`), não a última lida.

Ao corrigir o item 1, introduzi um terceiro bug — pego antes de qualquer
publicação: a alocação final vinha de um dicionário auxiliar
(`retido_em[crianca] = último estrato aceito`) que nunca era limpo quando a
criança era rejeitada depois sem conseguir vaga em outro lugar. Resultado:
1.039 dos 2.114 estratos apareciam com mais crianças alocadas que capacidade.
`held` (o estado real por rodada) nunca violava a capacidade; o retorno
final é que estava errado. Corrigido derivando a alocação final direto de
`held`, e não de um rastro incremental. **Verificação atual: 0 estratos
excedem capacidade, em qualquer fração de reserva testada.**

## Backtest: dois cenários, propositalmente separados

**Cenário A — mesma vaga que existiu de fato.** Capacidade por estrato =
número de crianças que o próprio processo de 2025 confirmou naquele estrato
(corrigido, ver bug 2). Mede só a **redistribuição**: mesmas vagas, ordem de
prioridade diferente.

**Cenário B — soma a vaga ociosa real** (do arquivo de oferta da SME, 8.290
vagas). Mede o **ganho líquido**: quantas crianças a mais são atendidas sem
construir nada.

Real 2025 (referência, corrigida): **48.675 confirmadas.**

| Reserva territorial | A · alocadas | A · ganharam | A · perderam | B · alocadas | B · ganharam | B · perderam |
|---:|---:|---:|---:|---:|---:|---:|
| 0% | 47.773 | 8.176 | 9.078 | 49.476 | 8.585 | 7.784 |
| 20% | 47.768 | 8.215 | 9.122 | 49.439 | 8.600 | 7.836 |
| 30% | 47.768 | 8.211 | 9.118 | 49.440 | 8.611 | 7.846 |
| **35%** | 47.760 | 8.184 | 9.099 | **49.448** | 8.601 | 7.828 |
| 40% | 47.765 | 8.194 | 9.104 | 49.452 | 8.604 | 7.827 |
| 50% | 47.767 | 8.216 | 9.124 | 49.454 | 8.631 | 7.852 |
| 70% | 47.791 | 8.229 | 9.113 | 49.477 | 8.650 | 7.848 |
| 100% | 47.805 | 8.253 | 9.123 | 49.486 | 8.661 | 7.850 |

**A fração de reserva deixou de afetar o volume.** Com aceitação diferida e
reserva mole, a diferença entre 0% e 100% de reserva é de ~45 crianças em
quase 48 mil (0,1%) — dentro do ruído. Isso **não é o mesmo achado** da
versão anterior deste documento (que reportava um platô em 30-40% com queda
nos extremos): aquele resultado era artefato dos três passes, que
desperdiçavam vaga reservada nos extremos. Corrigido o mecanismo, o
desperdício desaparece e a fração de reserva para de ser uma alavanca de
volume.

**Mas a fração de reserva continua importando — só que para outra coisa: o
trade-off entre dois eixos de equidade**, não entre volume e nada:

| Reserva | Alocadas | No próprio bairro | CadÚnico atendidas | 1ª opção |
|---:|---:|---:|---:|---:|
| 0% | 49.476 | 55,1% | 94,0% | 84,3% |
| 35% | 49.448 | 60,3% | 93,1% | 84,1% |
| 70% | 49.477 | 63,3% | 91,4% | 83,5% |
| 100% | 49.486 | 65,2% | 90,1% | 82,8% |

Mais reserva = mais crianças atendidas perto de casa, à custa de menos
crianças CadÚnico atendidas (uma criança local de menor prioridade pode
tomar assento reservado de uma criança CadÚnico mais distante). **35% é um
ponto médio razoável nesse trade-off, não um ótimo de volume** — a decisão
de quanto pesar território contra prioridade socioeconômica é normativa, e
deveria ser explicitada, não escondida atrás de uma simulação.

### De onde vem o ganho líquido

Decompondo o cenário B (capacidade + vaga ociosa) a 35% de reserva:

| Fonte | Efeito no volume |
|---|---:|
| Mecanismo (dedup por criança) + vaga ociosa, sem régua nem reserva | **+968** |
| Régua (pontuação vs sorteio puro) | **−172 a −197** |
| Reserva territorial | **−17 a +8** (ruído) |
| **Total (régua + reserva + mecanismo)** | **+779** |

A régua e a reserva custam volume — pequeno, mas custam, porque forçam a
alocação a respeitar prioridade e território em vez de maximizar contagem
pura. **Isso é esperado e correto: a régua não existe para aumentar volume,
existe para decidir quem é atendido.** E nisso o ganho é grande — ver
próxima seção.

## A régua usada é a régua real, não uma proxy

O `pontos` que ordena a fila global vem da **régua legal de 2025 inteira**
(`Query C`, 13 critérios somando 100 pontos), não só do CadÚnico. Os pesos
2025, do maior ao menor:

| Critério | Pontos |
| --- | ---: |
| Inscrito no CadÚnico | 51 |
| Público-alvo da educação especial | 25 |
| Violência doméstica no convívio | 4 |
| Família monoparental | 4 |
| Responsável com deficiência | 3 |
| Doença crônica grave na família | 3 |
| Uso abusivo de drogas/álcool na família | 2 |
| Ex-presidiário há até 5 anos na família | 2 |
| Refugiado | 2 |
| Já esperou na fila no ano anterior sem atendimento | 2 |
| Bolsa Família ou Cartão Carioca | 2 |

Mais dois critérios de **desempate** (não pontuados, `perg_criterio='Sim'`,
estáveis nos 5 anos): irmão matriculado na rede, pais/responsáveis menores
de 18 anos. O motor original ignorava os dois — a régua real tem cinco
degraus de prioridade, não dois. Com 31,75% das crianças empatadas em 0
pontos, isso decide a maior parte da fila. Efeito medido, dentro do bloco de
20.184 crianças em 0 pontos: ter irmão na rede muda a chance de vaga de
**56,6% para 67,0%**.

São todos critérios socioeconômicos e de vulnerabilidade — nenhum é
território ou proximidade. A reserva territorial é um eixo **ortogonal** a
essa régua: primeiro a criança compete no mérito socioeconômico (que já
embute a proteção a quem mais precisa), depois, só para quem não entrou por
mérito, o território dá uma segunda chance. Não duplica proteção,
complementa — e ordenar por ela leva as crianças que declararam CadÚnico de
78,0% para **93,1%** de atendimento (cenário B, 35% de reserva).

**Checagem feita e descartada:** cheguei a supor que a pontuação variava
entre as opções de uma mesma criança (por causa da verificação manual de
CadÚnico por unidade, P3) e cheguei a alterar o motor para usar o máximo
entre as opções. Verificação mais cuidadosa mostrou que isso está errado:
dentro do mesmo cadastro real `(prm_id,plm_id,ipl_id)`, a pontuação é
**100% constante — 0 de 71.930 cadastros de 2025 têm pontos diferentes
entre opções**. A régua é aplicada à família uma vez, não por opção, como
esperado. O motor foi revertido para a versão original (usa o único valor
de pontos do cadastro).

O que eu tinha confundido com "inconsistência entre opções" era, na
verdade, **431 códigos `aluno_anon` que correspondem a mais de um cadastro
real diferente** (média de 2,16 cadastros por código afetado, contra 1,14
nos códigos sem inconsistência) — ou seja, colisão de identidade, o mesmo
fenômeno do P5, só que dentro do mesmo ano e não capturado pelo teste de
sexo/nascimento usado lá. Isso reforça P5, não é um achado novo de P3; já
está somado como mais um sinal de colisão em `PROBLEMAS.md`.

## O achado que muda a implementação: churn

Em todos os cenários, entre **7.800 e 9.100 crianças que hoje têm vaga
confirmada perderiam essa vaga** sob a nova regra — mesmo no cenário B, que
tem ganho líquido positivo.

Isso não é bug, é a régua fazendo o que a lei manda: hoje o desempate é a
data de inscrição, que não tem respaldo legal nenhum; a nova régua prioriza
por pontuação, os dois critérios legais de desempate e território. Quem
está confirmado hoje só porque confirmou antes de alguém com mais prioridade
perde o lugar para essa pessoa.

**Isso é inaceitável como corte geral.** Uma criança já matriculada e
frequentando fisicamente uma creche não pode ser desalocada por um
recálculo. A régua não pode ser aplicada retroativamente sobre quem já está
com vaga confirmada.

### Mitigação: aplicar só a partir de agora

- **Vagas já confirmadas ficam.** O motor de matching roda apenas sobre:
  (a) a fila de espera atual, e (b) vagas que ainda não têm ninguém
  confirmado ou que abrirem de agora em diante.
- **Coortes futuras entram direto pela nova regra**, sem histórico para
  reconciliar.
- Isso também atende de frente ao requisito do briefing: *"garantir
  agilidade e evitar gargalos, sem comprometer o fluxo contínuo de
  matrículas."* Não há corte geral, há transição gradual pela rotatividade
  natural de vagas.

## Caminho de produção

- Entrada: `pessoa_fisica` (RMI) para endereço/CPF, `Query C` para a régua do
  processo vigente, fila viva do sistema de inscrição.
- Execução: job agendado (Prefect, que a IplanRio já opera) rodando o mesmo
  algoritmo — trivial de portar, é laço sobre listas ordenadas, não precisa de
  solver.
- Rodada principal no fechamento do período de inscrição; rodadas
  incrementais (quinzenais) sobre o resíduo, reaproveitando o mesmo código.
- Saída: lista de alocação → alimenta a fila de convocação do Eixo 3.

## Em aberto

- Reserva por **microárea da SME**, não por bairro (mais fino, mais correto
  territorialmente) — o backtest usou bairro porque é o campo disponível
  direto na Query A; produção deveria testar microárea, e território
  deveria idealmente ser por distância (lat/long via RMI), não por polígono
  administrativo — bairros do Rio têm tamanho muito heterogêneo (Campo
  Grande tem quilômetros, Copacabana é minúscula).
- Irmãos: alocação conjunta não está implementada nesta versão — o critério
  hoje só desempata, não garante ficarem juntos.
- A fração de reserva não é mais um ótimo de volume (ver acima); é uma
  escolha normativa entre equidade territorial e prioridade socioeconômica.
  35% é um ponto médio razoável, não um valor calibrado por simulação.
- Pontuação declarada vs confirmada continua em aberto e é dependência do
  P3: o motor ordena por pontuação **declarada** porque a confirmada hoje é
  destruída pela verificação manual (ver P3 em `PROBLEMAS.md`).
