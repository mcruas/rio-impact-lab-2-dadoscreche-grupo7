# Resumo de impacto: Match Creche

Um sistema com quatro etapas que trabalham juntas: a família é bem orientada
na escolha, o algoritmo aloca de forma justa e eficiente, a vaga é confirmada
sem depender de ligação manual, e a família responde sem sair do WhatsApp.

## As quatro etapas

1. **Recomendação de escola** — sugere creches reais perto de casa, com
   distância calculada de verdade.
2. **Motor de match (Gale-Shapley)** — decide quem fica com qual vaga, de
   forma justa e à prova de "jogadinha".
3. **Convocação automática (RMI + WhatsApp)** — avisa a família e confirma a
   vaga sem depender de o diretor ligar pra cada uma.
4. **IA no contato** — a família responde em linguagem natural, no próprio
   WhatsApp, sem precisar voltar ao site.

---

## 1. Recomendação de escola

Mostra pra família as creches mais próximas de casa de verdade — usando a
localização real do CEP, não uma aproximação por bairro. **Erro de distância
caiu de 0,97km para 0,65km.** Isso ajuda a família a listar mais opções com
confiança, o que importa muito mais a partir da etapa 2.

## 2. Motor de match: o que é o Gale-Shapley

É o mesmo algoritmo (aceitação diferida) usado hoje na matrícula pública de
Nova York, Boston e no processo nacional de admissão escolar do Chile — rendeu
o Nobel de Economia de 2012 aos seus criadores. A ideia é simples:

- Cada criança "propõe" pra sua creche preferida.
- Cada creche só aceita as melhores propostas até a vaga acabar — e pode
  **trocar** uma criança já aceita por outra melhor que apareça depois.
- O processo repete até sobrar ninguém propondo.

O resultado tem duas garantias fortes: **ninguém ganha vantagem escondendo
opções ou mentindo preferência** (ao contrário do sistema antigo, em que listar
menos opções podia dar resultado melhor), e **nenhuma vaga fica presa** com uma
criança pior alocada enquanto uma criança melhor colocada quer aquela vaga.

**Resultado, rodando sobre as 62.891 crianças reais de 2025:**

- **+779 crianças atendidas a mais**, somando o conserto de um bug de
  contagem de capacidade (531 vagas que existiam mas não eram contadas), o
  aproveitamento de vaga ociosa e a nova régua de prioridade.
- Famílias que declaram CadÚnico saem de **78,0% para 93,1%** de chance de
  atendimento — a régua de prioridade legal (hoje ignorada na prática) passa
  a valer de verdade.
- **Ninguém que já tem vaga confirmada perde ela**: a régua nova só vale pra
  fila de espera e vagas novas, nunca aplicada pra trás.

## 3. Convocação automática (RMI + WhatsApp)

Hoje a confirmação de vaga é manual: o diretor liga, manda SMS, manda
WhatsApp, um por um. Automatizamos isso: o sistema convoca pelo telefone mais
confiável (via RMI) e, se a resposta for "não sou eu", passa sozinho pro
próximo telefone da família — sem intervenção humana.

E ninguém fica esperando pra sempre: sem resposta em 48h já conta como
recusa e avança a fila; se passar de 5 dias sem confirmação nenhuma, a vaga é
liberada de verdade e o motor de match roda de novo — **em lote, sobre ~63 mil
famílias, em ~1,1 segundo** — passando a vaga pra próxima criança da fila.

## 4. IA no contato

A resposta da família é interpretada pelo LLM que já atende o WhatsApp da
Prefeitura — não criamos canal novo. Pra confirmar de verdade (e evitar
número reciclado ou compartilhado), o sistema pede só os últimos dígitos do
CPF da criança, direto na conversa. A família nunca precisa voltar ao site.

---

**Em uma frase:** melhor escolha, melhor algoritmo, melhor confirmação, sem
fricção — da inscrição até a matrícula de fato acontecer.
