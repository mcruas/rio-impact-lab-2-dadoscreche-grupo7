# Arquitetura de contato: RMI + WhatsApp da Prefeitura

Decisão: **não construir sistema de notificação.** A Prefeitura já tem a
infraestrutura inteira, documentada em `docs.dados.rio`. Nosso entregável se
encaixa nela em vez de competir com ela.

## O que já existe

| Peça | O que é | Onde |
| --- | --- | --- |
| **RMI — Pessoa Física** | Cadastro unificado por CPF: nome, nome social, endereço principal **com latitude e longitude**, endereços alternativos | `rj-crm-registry.rmi_dados_mestres.pessoa_fisica` |
| **RMI — Telefone** | Registro consolidado de telefones, com qualidade técnica, confiança de propriedade e histórico de aparições por sistema | `rj-crm-registry.rmi_dados_mestres.telefone` |
| **Disparo WhatsApp** | WhatsApp Business API via fornecedor **Wetalkie**, orquestrado por Prefect, operado pela IplanRio | `docs.dados.rio/disparos-whatsapp` |
| **APIs de telefone** | opt-in, opt-out, quarentena, vínculo telefone↔CPF, cidadão por telefone | Barramento / API Reference |

## O que isso muda no nosso desenho

**1. Endereço deixa de ser aproximação.** O `pessoa_fisica.endereco.principal`
traz latitude e longitude. Toda a lógica territorial — sugestão de unidade por
proximidade (P1), reserva territorial no matching, overbooking calibrado por
distância — deixa de usar centroide de bairro e passa a usar o ponto real.

No hackathon seguimos com centroide, porque a base anonimizada só expõe
bairro/CEP. Em produção o mesmo código recebe coordenada e fica mais preciso.

**2. "Contato desatualizado" tem solução pronta.** A tabela `telefone` já traz
`telefone_qualidade`, `confianca_propriedade` e `telefone_aparicoes` com a data da
última aparição em cada sistema municipal. A cascata de contato deixa de ser
tentativa cega e passa a ser ordenada por confiança.

**3. O disparo já sabe para quem não mandar.** Existe uma coluna
`estrategia_envio` pré-calculada; a documentação exige filtrar apenas `ENVIAR` ou
`TESTAR`, porque as demais categorias derrubam a qualidade do número de WhatsApp
da Prefeitura. Não precisamos inventar heurística de deliverability.

## Qual é o nosso entregável, então

Não é um integrador de WhatsApp. São três coisas pequenas:

1. **Uma query BigQuery** que devolve a fila de convocação já resolvida, no
   contrato exigido pela pipeline: JSON com as chaves `celular_disparo`,
   `externalID` e `vars`.
2. **Um template HSM** de convocação de vaga, com as variáveis certas (primeiro
   nome via `FORMAT_NAME`, priorizando `nome_social`; unidade; prazo; endereço).
3. **O log de eventos** que hoje não existe — usando o `externalID` como chave de
   rastreio e a resposta da URA como fechamento do ciclo.

O item 3 é o que resolve o gap que a própria SME aponta: *"não há registro de
quando uma opção mudou de status"*. Com `externalID` amarrando convocação →
entrega → resposta, o SLA por criança passa a ser mensurável.

## Fluxo de convocação: cascata de telefones + confirmação por chat

Hoje esse contato é manual: SMS, WhatsApp e e-mail disparados um a um pelo
diretor da unidade. O que este módulo (`modulos/acompanhamento/`, Eixo 3)
automatiza é a **cascata de tentativa e a confirmação**, não o disparo em si
(que continua governado pela IplanRio, ver restrições abaixo).

**Gatilho.** Quando o Motor de Match aloca uma vaga (`status=Confirmado` em
`GET /status/{cpf}`), o Eixo 3 dispara o HSM de convocação para o telefone de
maior confiança da cascata do responsável (tabela `telefone`, ordenada por
`telefone_qualidade`/`confianca_propriedade`, filtrada por
`estrategia_envio IN ('ENVIAR','TESTAR')`).

**Resposta processada pelo LLM que já existe no WhatsApp da Prefeitura.** Não
construímos um novo canal de conversa — o mesmo LLM que já atende outras
exposições via Wetalkie interpreta a resposta em linguagem natural e chama o
nosso webhook (`POST /convocacoes/{cpf}/eventos`) com uma intenção estruturada:

- **"Não sou eu"** → esse telefone não pertence à pessoa certa. A cascata
  avança para o próximo telefone do RMI e reenvia o HSM. Isso substitui o que
  hoje é o diretor testando manualmente SMS depois WhatsApp depois e-mail.
- **"Confirmo"** → antes de fechar o ciclo, o LLM pede só os **últimos 4
  dígitos do CPF da criança** — pouco atrito, sem forçar o responsável a
  voltar ao site — e repassa junto com a intenção. Isso existe porque um
  número de telefone pode ter sido **reciclado ou compartilhado**: "confirmo"
  vindo da pessoa errada não pode fechar a vaga de outra família. Dígito
  batendo com o CPF real (RMI, em produção) → `Confirmada`. Dígito errado é
  tratado exatamente como "não sou eu": a cascata avança, não é encerrada como
  erro.
- **Cascata esgotada** (nenhum telefone confirmou) → `EsgotadoEscalarManual`,
  volta para o fluxo humano do diretor. Isso é o piso de hoje, não uma
  regressão: a automação cobre o caso comum, o caso raro cai de volta no
  processo atual.

**Contrato e estados**: `contracts/acompanhamento.openapi.yaml`
(`POST /convocacoes/{cpf}`, `GET /convocacoes/{cpf}`,
`POST /convocacoes/{cpf}/eventos`) e `contracts/schemas/convocacao.schema.json` /
`evento_convocacao.schema.json`. Implementação de referência em
`modulos/acompanhamento/backend/main.py`, testada de ponta a ponta contra o
Motor de Match real (cascata avançando em "não sou eu", confirmação com
dígito certo/errado, escalonamento ao esgotar).

**O que é real e o que é simulado nesta implementação de hackathon:** a
máquina de estados e o contrato são os que valeriam em produção. O que é
mock, porque a base anonimizada não tem CPF nem telefone reais: o tamanho da
cascata de telefones (fixo em 3, cadastrado no código) e os "últimos 4
dígitos do CPF" (gerados por hash do código anonimizado, não dígitos de CPF
de verdade). Plugar no RMI de verdade troca só essas duas peças, não a
máquina de estados.

## Restrições reais, para não prometer demais

- **HSM é template aprovado previamente.** Não dá para improvisar texto: a
  mensagem precisa estar cadastrada em `crm_whatsapp.mensagem_ativa` com ID.
- **O disparo tem gente no meio.** A documentação descreve whitelist, liberação
  de contatos por um responsável e sinal verde antes do envio. Hoje é um processo
  governado, não um gatilho autônomo. "Automatizar" aqui significa automatizar a
  **fila e o rastreio**, com o disparo seguindo a governança da IplanRio.
- **Opt-in.** Existe API de opt-in/opt-out e quarentena. Convocação de vaga
  provavelmente se enquadra como mensagem de utilidade, mas isso precisa ser
  confirmado com a IplanRio — não é decisão nossa.
- **Precisamos de CPF.** A base do hackathon é anonimizada e não tem CPF; o
  vínculo com o RMI só existe em produção. A inscrição real já exige CPF com
  validação na Receita Federal, então o caminho existe.

## Referências

- Índice para máquina: `https://docs.dados.rio/llms.txt`
- Padrões de disparo: `https://docs.dados.rio/disparos-whatsapp/padronizacao-query`
- RMI Pessoa Física: `https://docs.dados.rio/rmi/dados-mestres/pessoa-física`
- RMI Telefone: `https://docs.dados.rio/rmi/dados-mestres/telefone`
- OpenAPI: `https://docs.dados.rio/api-specs/rmi-openapi.json`
