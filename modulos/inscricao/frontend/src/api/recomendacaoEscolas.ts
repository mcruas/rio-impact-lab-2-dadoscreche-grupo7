// Cliente do backend modulos/recomendacao-escolas (contrato em
// contracts/recomendacao-escolas.openapi.yaml). URL configurável via env pra
// funcionar tanto local (uvicorn) quanto depois de deploy (Vercel) sem mudar código.

import type { RecomendacaoEscola } from "../types";

const BASE_URL = import.meta.env.VITE_API_RECOMENDACAO_URL ?? "http://localhost:8000";

export class ErroApiRecomendacao extends Error {}

export interface LocalizacaoCep {
  bairro: string;
  /** Nulas quando o CEP só existe no ViaCEP, que não devolve coordenada. */
  latitude: number | null;
  longitude: number | null;
}

export async function resolverCep(cep: string): Promise<LocalizacaoCep | null> {
  const resp = await fetch(`${BASE_URL}/cep/${encodeURIComponent(cep)}`);
  if (resp.status === 404) return null;
  if (!resp.ok) throw new ErroApiRecomendacao(`Falha ao consultar CEP (HTTP ${resp.status})`);
  const dados = (await resp.json()) as {
    bairro: string;
    latitude?: number | null;
    longitude?: number | null;
  };
  return {
    bairro: dados.bairro,
    latitude: dados.latitude ?? null,
    longitude: dados.longitude ?? null,
  };
}

interface RecomendacaoEscolaApi {
  esc_codigo: string;
  nome: string;
  endereco: string | null;
  bairro: string;
  latitude: number | null;
  longitude: number | null;
  tipo: string | null;
  distancia_km: number;
  origem_distancia: string;
  indice_concorrencia: number | null;
  preferida: boolean;
  pontuacao_final: number;
  rationale: {
    pontos_proximidade: number;
    pontos_adequacao_score: number;
    pontos_historico: number;
    explicacao: string;
  };
}

function mapearResposta(item: RecomendacaoEscolaApi): RecomendacaoEscola {
  return {
    escCodigo: item.esc_codigo,
    nome: item.nome,
    endereco: item.endereco,
    bairro: item.bairro,
    latitude: item.latitude,
    longitude: item.longitude,
    tipo: item.tipo,
    distanciaKm: item.distancia_km,
    origemDistancia: item.origem_distancia,
    indiceConcorrencia: item.indice_concorrencia,
    preferida: item.preferida,
    pontuacaoFinal: item.pontuacao_final,
    rationale: {
      pontosProximidade: item.rationale.pontos_proximidade,
      pontosAdequacaoScore: item.rationale.pontos_adequacao_score,
      pontosHistorico: item.rationale.pontos_historico,
      explicacao: item.rationale.explicacao,
    },
  };
}

// O contrato (contracts/schemas/endereco.schema.json) exige cep no formato
// ^[0-9]{8}$ — sem hífen. Manda só quando sobrarem exatamente 8 dígitos; qualquer
// outra coisa vira undefined e o backend cai no centróide do bairro.
function cepParaContrato(cep?: string): string | undefined {
  const digitos = (cep ?? "").replace(/\D/g, "");
  return digitos.length === 8 ? digitos : undefined;
}

export async function buscarPorBairro(
  bairro: string,
  limite = 8,
  cep?: string,
): Promise<RecomendacaoEscola[]> {
  // Mandar o cep junto do bairro é o que dá precisão de CEP (erro mediano 0,65 km)
  // em vez de precisão de bairro (0,97 km) — ver modulos/recomendacao-escolas/app/ceps.py.
  const cepNormalizado = cepParaContrato(cep);
  const resp = await fetch(`${BASE_URL}/recomendacoes?limite=${limite}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enderecos: [{ tipo: "Moradia", bairro, ...(cepNormalizado ? { cep: cepNormalizado } : {}) }],
    }),
  });
  if (!resp.ok) {
    throw new ErroApiRecomendacao(`Falha ao buscar recomendações (HTTP ${resp.status})`);
  }
  const dados = (await resp.json()) as RecomendacaoEscolaApi[];
  return dados.map(mapearResposta);
}
