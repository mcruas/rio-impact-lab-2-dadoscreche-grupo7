// Espelha (de forma simplificada, focada em UI) as entidades de
// contracts/schemas/*.schema.json.

export type Turno = "Integral" | "Parcial";

export type RespostaPrioridade = "Sim" | "Nao" | "NaoSei";

export type ModoBusca = "creche" | "regiao";

export interface DadosInscricao {
  nomeCrianca: string;
  cpfCrianca: string;
  dataNascimento: string;
  turno: Turno | null;
  cpfResponsavel: string;
  cepResidencial: string;
  modoBusca: ModoBusca;
  buscaTexto: string;
  /** escCodigo em ordem de preferência (até 5) — chave pra olhar em resultadosBusca. */
  crechesEscolhidas: string[];
  /** Candidatas trazidas pela última busca (passo 2) — fonte de verdade dos
   * dados exibidos no passo 3 (inclui candidatas fora do top 5 escolhido,
   * usadas pela sugestão de troca). Real (POST /recomendacoes) no modo
   * "regiao"; mockado no modo "creche" (ver data/mockCreches.ts). */
  resultadosBusca: RecomendacaoEscola[];
  cadUnico: RespostaPrioridade | null;
  bolsaFamilia: RespostaPrioridade | null;
  publicoEducacaoEspecial: "Sim" | "Nao" | null;
  outraVulnerabilidade: "Sim" | "Nao" | null;
}

export const dadosIniciais: DadosInscricao = {
  nomeCrianca: "",
  cpfCrianca: "",
  dataNascimento: "",
  turno: null,
  cpfResponsavel: "",
  cepResidencial: "",
  modoBusca: "regiao",
  buscaTexto: "",
  crechesEscolhidas: [],
  resultadosBusca: [],
  cadUnico: null,
  bolsaFamilia: null,
  publicoEducacaoEspecial: null,
  outraVulnerabilidade: null,
};

// Espelha contracts/schemas/recomendacao_escola.schema.json — mesmo shape
// tanto pra resultado real (POST /recomendacoes) quanto pro fallback
// mockado de "buscar por creche" (nome), pra Step3 renderizar os dois igual.
export interface Rationale {
  pontosProximidade: number;
  pontosAdequacaoScore: number;
  pontosHistorico: number;
  explicacao: string;
}

export interface RecomendacaoEscola {
  escCodigo: string;
  nome: string;
  endereco: string | null;
  bairro: string;
  tipo: string | null;
  distanciaKm: number;
  origemDistancia: string; // "Moradia" | "Trabalho" | outro tipo de local
  indiceConcorrencia: number | null;
  preferida: boolean;
  pontuacaoFinal: number;
  rationale: Rationale;
}
