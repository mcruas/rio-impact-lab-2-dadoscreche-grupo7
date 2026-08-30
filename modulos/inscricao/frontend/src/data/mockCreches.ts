import type { DadosInscricao, RecomendacaoEscola } from "../types";

// Fallback só do modo "buscar por creche" (nome) — o backend recomendacao-escolas
// não tem busca por nome nesta rodada (só por bairro/CEP, que já é real — ver
// src/api/recomendacaoEscolas.ts). Mesmo shape de RecomendacaoEscola pra Step3
// renderizar igual não importa a origem, mas sem inventar distância/pontuação:
// isso é resultado de nome, não de proximidade.
const POOL_BUSCA_POR_NOME: RecomendacaoEscola[] = [
  { escCodigo: "208601", nome: "Creche Alegria do Saber", bairro: "Campo Grande" },
  { escCodigo: "208602", nome: "EDI Recanto da Criança", bairro: "Campo Grande" },
  { escCodigo: "208603", nome: "EDI Coelhinho Tarado", bairro: "Campo Grande" },
  { escCodigo: "208604", nome: "Creche Mundo Infantil", bairro: "Realengo" },
  { escCodigo: "208605", nome: "EDI Pequenos Passos", bairro: "Bangu" },
  { escCodigo: "208606", nome: "Creche Cantinho Feliz", bairro: "Campo Grande" },
  { escCodigo: "208607", nome: "EDI Estrela Guia", bairro: "Santa Cruz" },
].map((base) => ({
  ...base,
  endereco: null,
  latitude: null,
  longitude: null,
  tipo: "Creche",
  distanciaKm: 0,
  origemDistancia: "Nome buscado",
  indiceConcorrencia: null,
  preferida: false,
  pontuacaoFinal: 0,
  rationale: {
    pontosProximidade: 0,
    pontosAdequacaoScore: 0,
    pontosHistorico: 0,
    explicacao:
      "Resultado por nome da creche — sem cálculo de proximidade (busca por bairro/CEP calcula distância de verdade).",
  },
}));

export function buscarCrechesPorNome(texto: string): RecomendacaoEscola[] {
  const termo = texto.trim().toLowerCase();
  if (termo === "") return POOL_BUSCA_POR_NOME.slice(0, 5);
  const filtradas = POOL_BUSCA_POR_NOME.filter((creche) => creche.nome.toLowerCase().includes(termo));
  return (filtradas.length > 0 ? filtradas : POOL_BUSCA_POR_NOME).slice(0, 5);
}

// Usado pelo botão "Preencher com dados de teste" (ver App.tsx/PainelTeste) —
// preenche os campos simples sem rede. Não simula um resultado de busca: o
// passo 3 só tem conteúdo depois que o usuário buscar de verdade no passo 2.
export const DADOS_EXEMPLO: DadosInscricao = {
  nomeCrianca: "Maria Eduarda da Silva",
  cpfCrianca: "123.456.789-09",
  dataNascimento: "2023-05-02",
  turno: "Integral",
  cpfResponsavel: "987.654.321-00",
  cepResidencial: "23050-300",
  // Resolvidas de verdade no passo 2, ao buscar pelo CEP acima.
  latFamilia: null,
  lonFamilia: null,
  modoBusca: "regiao",
  buscaTexto: "23050-300",
  crechesEscolhidas: [],
  resultadosBusca: [],
  cadUnico: "Sim",
  bolsaFamilia: "Sim",
  publicoEducacaoEspecial: "Nao",
  outraVulnerabilidade: "Nao",
  // Escolhido pela família na tela 7, não é dado do formulário de inscrição.
  envioDocumentos: null,
};
