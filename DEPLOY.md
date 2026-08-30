# Match Creche (ao vivo)

- **Site**: https://inscricao-frontend-production.up.railway.app
- **Backend**: https://inscricao-backend-production-3e24.up.railway.app

## O problema que a rede enfrenta hoje

A rede municipal recebe milhares de inscrições por processo, sem um
mecanismo de alocação à prova de estratégia, sem visibilidade de quanto
tempo uma vaga oferecida fica esperando confirmação, e com a confirmação
inteira dependendo de ligação manual do diretor — SMS, WhatsApp, e-mail, um
a um. O resultado: vagas que existem ficam subutilizadas, a régua de
prioridade legal (CadÚnico, Bolsa Família, educação especial etc.) não é
aplicada de forma consistente, e famílias vulneráveis — justamente as que a
régua deveria proteger — são as que mais perdem vaga por não conseguir
comparecer a tempo num processo presencial.

O Match Creche é o sistema de ponta a ponta que resolve isso: a família
escolhe melhor informada, o algoritmo aloca de forma justa e eficiente, a
confirmação de vaga acontece sozinha, e ninguém precisa sair do WhatsApp
pra confirmar.

## As vitórias para a rede

**Mais crianças atendidas com a mesma capacidade.** Rodando sobre as 62.891
crianças reais de 2025, o motor corrigido atende **+779 crianças a mais**
sem abrir uma vaga nova — só corrigindo um bug que subcontava 531 vagas já
existentes e aproveitando vaga ociosa que o mecanismo antigo desperdiçava.
Ganho de eficiência puro, sem custo de expansão.

**A régua de prioridade passa a valer de verdade.** Hoje ela é praticamente
ignorada na prática porque o mecanismo de alocação não é matching de
verdade. Com o motor corrigido, famílias que declaram CadÚnico saem de
**78,0% para 93,1%** de chance de atendimento — a rede passa a proteger
quem a lei manda proteger, e não só quem chegou primeiro no balcão.

**Ninguém que já tem vaga perde ela.** A régua nova só vale pra fila de
espera e vagas futuras, nunca aplicada pra trás — a rede pode adotar o
mecanismo novo sem reabrir nenhuma matrícula já confirmada.

**Vaga parada vira vaga ocupada, em segundos, não em semanas.** Hoje uma
vaga "selecionada" aguardando confirmação pode ficar presa indefinidamente
enquanto o diretor tenta contato manual. O sistema convoca sozinho pelo
telefone mais confiável (via RMI), avança pro próximo telefone se a
resposta for "não sou eu", e sem resposta em 48h já avança a fila. Passado
5 dias sem confirmação nenhuma, a vaga é liberada de verdade e o motor
recalcula a alocação inteira — **~63 mil famílias em ~1,1 segundo** — sem
esperar o próximo ciclo administrativo.

**A confirmação deixa de ser uma barreira presencial.** A família responde
pelo próprio WhatsApp, interpretado pelo LLM que a Prefeitura já usa —
nenhum canal novo, nenhum aplicativo novo, nenhuma exigência de comparecer
num horário comercial. Isso importa porque essa exigência hoje filtra
primeiro quem tem menos flexibilidade de horário e menos acesso a
transporte — exatamente as famílias que a régua de prioridade existe para
proteger.

**A família escolhe informada, não só pela creche que já conhece.** A
recomendação geocodifica o CEP de verdade (erro de distância caindo de
0,97km para 0,65km) e mostra opções reais mais próximas de casa. Isso só
se traduz em mais chance de vaga porque o motor corrigido garante que
listar mais opções nunca piora o resultado da família — no mecanismo
antigo, listar menos podia dar resultado melhor, o oposto do que se pedia
à família.

## O papel do RMI

Decisão de arquitetura: não construir um sistema de notificação novo — a
Prefeitura já tem essa infraestrutura pronta, e o Match Creche se encaixa
nela em vez de competir com ela. O RMI (Registro Municipal de Informações)
é o cadastro unificado da cidade, e ele resolve dois problemas reais que
hoje custam vaga:

**A cascata de telefone deixa de ser tentativa cega.** O RMI mantém um
registro consolidado de telefone por CPF, com qualidade técnica, confiança
de propriedade e histórico de quando cada número apareceu em qual sistema
municipal. A convocação usa exatamente essa ordem — tenta primeiro o
telefone mais confiável, não o mais recente cadastrado ou o primeiro da
lista — e é isso que faz a cascata avançar rápido pro número certo em vez
de insistir em contatos desatualizados.

**O endereço deixa de ser aproximação.** O RMI traz o endereço principal da
família já com latitude e longitude reais, não só bairro ou CEP. Toda a
lógica de proximidade — recomendação de escola, reserva territorial no
matching — passa a calcular sobre o ponto real da família, não sobre um
centróide de bairro. (No ambiente de teste seguimos com a aproximação por
CEP porque a base de dados usada aqui é anonimizada e só expõe essa
granularidade; em produção, plugando no RMI de verdade, o mesmo código já
fica mais preciso sem precisar ser reescrito.)

## Como é feito o matching, em uma frase

Aceitação diferida (Gale-Shapley) — o mesmo mecanismo usado hoje na
matrícula pública de Nova York, Boston, e no processo nacional de admissão
do Chile, e que rendeu o Nobel de Economia de 2012 aos seus criadores.
Cada criança propõe pra sua creche preferida; cada creche só segura as
melhores propostas até a vaga acabar, podendo trocar uma criança aceita
por outra melhor que apareça depois; repete até não sobrar ninguém
propondo. Resultado: nenhuma vaga fica presa com uma criança pior colocada
enquanto uma criança melhor colocada ainda a quer, e ninguém ganha vantagem
escondendo opções verdadeiras.
