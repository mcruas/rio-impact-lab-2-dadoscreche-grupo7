# Resumo de impacto: Match Perfeito

Quatro peças que se encaixam numa coisa só: fazer a vaga certa chegar na
criança certa, e a confirmação realmente acontecer.

## 1. Recomendação de escola (upstream)

47,0% das famílias listam uma única creche (P1) — em geral a mais próxima ou
conhecida, mesmo havendo vaga ociosa ao lado. `recomendacao-escolas/` sugere
unidades a partir do endereço real: geocodificação por CEP em vez de
centróide de bairro (erro mediano cai de 0,97km para 0,65km). Sozinha, essa
sugestão rende pouco — listar mais opções hoje só aumenta a chance de vaga em
2,6 pontos percentuais, porque a classificação atual não é um matching de
verdade. É aí que a peça 2 entra.

## 2. Motor de match corrigido

O motor antigo tinha dois defeitos reais, achados e corrigidos: não era à
prova de estratégia (truncar a lista de opções melhorava o resultado — o
oposto do que P1 pede às famílias) e subcontava a capacidade real em 531
vagas. Corrigido para aceitação diferida de verdade, com reserva territorial
mole e os dois critérios legais de desempate que o motor antigo ignorava
(irmão na rede, responsável menor de 18 anos). Rodando sobre os 62.891
crianças reais de 2025: ordenar pela régua legal em vez de sorteio leva o
atendimento de quem declara CadÚnico de 78,0% para 93,1%. A régua não existe
pra aumentar volume — custa ~180 vagas, e isso é esperado — existe pra
decidir quem é atendido, e nisso o efeito é grande. Ganho líquido total
(mecanismo + vaga ociosa + régua + reserva): +779 crianças. Achado que virou
salvaguarda: entre 7.800 e 9.100 crianças já confirmadas hoje perderiam a
vaga sob a nova ordem, então a régua nova só vale para a fila de espera e
vagas futuras — nunca aplicada retroativamente sobre quem já está matriculado.

Aceitação diferida (Gale-Shapley) não é uma aposta nova: é o mecanismo usado
hoje na matrícula das redes públicas de Nova York e Boston, e no processo
nacional de admissão escolar do Chile — uso consolidado o suficiente em
educação para render o Nobel de Economia de 2012 a Alvin Roth e Lloyd
Shapley "pela teoria de alocações estáveis e a prática do desenho de
mercados". Referências: Abdulkadiroğlu & Sönmez, *School Choice: A Mechanism
Design Approach*, American Economic Review 2003 (doi:10.1257/000282803322157061);
Abdulkadiroğlu, Pathak & Roth, *The New York City High School Match*, AER
2005; Abdulkadiroğlu, Pathak, Roth & Sönmez, *The Boston Public School
Match*, AER 2005; nobelprize.org/prizes/economic-sciences/2012/press-release.

## 3. RMI + WhatsApp: convocação automática

Hoje a confirmação de vaga é manual — SMS, WhatsApp e e-mail disparados um a
um pelo diretor da unidade. O Eixo 3 automatiza a cascata: convoca pelo
telefone de maior confiança (RMI) e, se a resposta for "não sou eu", avança
sozinho pro próximo telefone. Ninguém fica esperando pra sempre: sem resposta
em 48h o sistema trata como recusa e avança a cascata; se o processo manual
também vencer o prazo (5 dias), a vaga é liberada de verdade — o motor de
match roda de novo, em lote, sobre ~63 mil famílias em ~1,1s, e passa a
próxima prioridade daquele estrato pra frente.

## 4. IA no contato: confirmar sem sair do WhatsApp

A resposta em linguagem natural é interpretada pelo LLM que já atende o
WhatsApp da Prefeitura (Wetalkie) — não construímos canal novo. Pra fechar o
ciclo, pede só os 4 últimos dígitos do CPF da criança (protege contra número
reciclado ou compartilhado), sem forçar a família a voltar ao site. Baixo
atrito é a mesma lógica de P3: qualquer barreira extra de comparecimento
filtra primeiro quem o critério de prioridade quer proteger.

## Por que as quatro juntas

Cada peça sozinha resolve uma fração do problema e depende da seguinte:
sugestão sem matching de verdade rende pouco (P1); matching correto sem
confirmação automática ainda perde vaga para famílias que nunca vão
aparecer (P2, P4); confirmação automática sem canal de baixo atrito
reproduz a mesma barreira presencial que a régua de prioridade existe para
remover (P3). As quatro juntas fecham o ciclo — da inscrição à matrícula
efetivada — sem reintroduzir a barreira presencial em nenhum ponto do
caminho.
