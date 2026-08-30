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
