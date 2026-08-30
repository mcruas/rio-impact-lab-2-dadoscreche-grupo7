# Deploy — Match Creche (ao vivo)

- **Site**: https://inscricao-frontend-production.up.railway.app
- **Backend**: https://inscricao-backend-production-3e24.up.railway.app

Tudo hospedado no Railway (projeto `grupo7-inscricao`): 1 banco Postgres +
2 serviços (backend e frontend). Nada em Vercel.

## O que o sistema faz, e o que ele já prova

O Match Creche ataca o processo de inscrição em creches da rede pública do
Rio em quatro frentes que trabalham juntas: a família escolhe melhor, o
algoritmo aloca melhor, a confirmação de vaga acontece sem depender de
ligação manual, e a família responde sem sair do WhatsApp.

**Recomendação de escola.** Em vez de aproximar a distância da família até
a creche pelo centróide do bairro, o sistema geocodifica o CEP de verdade.
O erro de distância caiu de 0,97km para 0,65km — a família vê a ordem certa
de opções mais próximas de casa, não uma aproximação grosseira.

**Motor de match, com Gale-Shapley (aceitação diferida).** É o mesmo
algoritmo usado hoje na matrícula pública de Nova York, Boston e no processo
nacional de admissão do Chile — rendeu o Nobel de Economia de 2012 aos seus
criadores. A ideia: cada criança propõe pra sua creche preferida, cada
creche só aceita as melhores propostas até a vaga acabar, e pode trocar uma
criança já aceita por outra melhor que apareça depois. Repete até não sobrar
ninguém propondo. Duas garantias fortes saem disso: ninguém ganha vantagem
escondendo opções (o sistema antigo recompensava listar menos creches — o
oposto do que se pede à família) e nenhuma vaga fica presa com uma criança
pior colocada enquanto uma criança melhor colocada ainda a quer. Rodando
sobre as 62.891 crianças reais de 2025: **+779 crianças atendidas a mais**
(conserto de um bug que subcontava 531 vagas existentes, aproveitamento de
vaga ociosa e a régua de prioridade legal valendo de verdade); famílias que
declaram CadÚnico saem de **78,0% para 93,1%** de chance de atendimento; e
quem já tem vaga confirmada não perde nada — a régua nova só vale pra fila
de espera e vagas futuras, nunca aplicada retroativamente.

**Convocação automática via RMI + WhatsApp.** Hoje a confirmação de vaga é
manual: o diretor liga, manda SMS, manda WhatsApp, um por um. O sistema
convoca sozinho pelo telefone mais confiável (via RMI) e, se a resposta for
"não sou eu", avança pro próximo telefone da família sem intervenção
humana. Ninguém fica esperando pra sempre: sem resposta em 48h já conta como
recusa e avança a cascata; passado 5 dias sem confirmação nenhuma, a vaga é
liberada de verdade e o motor de match roda de novo — em lote, sobre
~63 mil famílias, em ~1,1 segundo — passando a vaga pra próxima criança da
fila.

**IA no contato.** A resposta da família é interpretada pelo LLM que já
atende o WhatsApp da Prefeitura — não foi criado canal novo. Pra confirmar
de verdade (evitando número reciclado ou compartilhado), o sistema pede só
os últimos dígitos do CPF da criança, direto na conversa. A família nunca
precisa voltar ao site.

## O que foi feito nesta rodada de deploy

- **Persistência real do módulo Inscrição.** `POST /inscricoes` e
  `GET /inscricoes/{cpf}` saíram de stub e passaram a gravar/ler de um
  Postgres de verdade.
- **Backend unificado.** Os 4 backends de módulo (inscrição, recomendação
  de escola, motor de match, acompanhamento) continuam sendo 4 aplicações
  independentes por dentro — só passaram a rodar num único serviço Railway,
  cada uma no seu prefixo de endereço, sem misturar código nem persistência
  entre elas e sem quebrar a fronteira de contrato (continuam se chamando
  só por HTTP). Isso trocou 4 deploys por 1, sem trocar a arquitetura.
- **Frontend ligado de verdade.** O formulário de inscrição agora resolve o
  CEP residencial e envia a inscrição de verdade antes de mostrar a tela de
  sucesso — antes a tela final era só estática, sem enviar nada pro
  backend.
- **Frontend no ar.** Antes só rodava na máquina local; agora está
  publicado junto com o backend.
- **Rename**: "Matrícula Carioca" virou "Match Creche".
