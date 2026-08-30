// Espelha (de forma simplificada, focada em UI) as entidades de
// contracts/schemas/*.schema.json.

export type Turno = "Integral" | "Parcial";

export type RespostaPrioridade = "Sim" | "Nao" | "NaoSei";

export type ModoBusca = "creche" | "regiao";

export type EnvioDocumentos = "aplicativo" | "presencial";

export interface DadosInscricao {
  nomeCrianca: string;
  cpfCrianca: string;
  dataNascimento: string;
  turno: Turno | null;
  cpfResponsavel: string;
  cepResidencial: string;
  /** Coordenada do cepResidencial, resolvida por GET /cep/{cep} no passo 2.
   * Nula quando o CEP nao esta na tabela local (ai o mapa nao mostra a casa). */
  latFamilia: number | null;
  lonFamilia: number | null;
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
  /** Passo 7 (fluxo de match): como a família entrega os documentos. Fica aqui,
   * e não no estado local da tela, pra sobreviver ao voltar/avançar. */
  envioDocumentos: EnvioDocumentos | null;
}

export const dadosIniciais: DadosInscricao = {
  nomeCrianca: "",
  cpfCrianca: "",
  dataNascimento: "",
  turno: null,
  cpfResponsavel: "",
  cepResidencial: "",
  latFamilia: null,
  lonFamilia: null,
  modoBusca: "regiao",
  buscaTexto: "",
  crechesEscolhidas: [],
  resultadosBusca: [],
  cadUnico: null,
  bolsaFamilia: null,
  publicoEducacaoEspecial: null,
  outraVulnerabilidade: null,
  envioDocumentos: null,
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
  /** Coordenada da escola (WGS84). Nula no fallback mockado de busca por nome,
   * que nao tem geolocalizacao — o mapa simplesmente nao planta esses pinos. */
  latitude: number | null;
  longitude: number | null;
  tipo: string | null;
  distanciaKm: number;
  origemDistancia: string; // "Moradia" | "Trabalho" | outro tipo de local
  indiceConcorrencia: number | null;
  preferida: boolean;
  pontuacaoFinal: number;
  rationale: Rationale;
}
