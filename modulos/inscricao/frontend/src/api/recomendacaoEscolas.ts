// Cliente do backend modulos/recomendacao-escolas (contrato em
// contracts/recomendacao-escolas.openapi.yaml). URL configurável via env pra
// funcionar tanto local (uvicorn) quanto depois de deploy (Vercel) sem mudar código.

import type { RecomendacaoEscola } from "../types";

const BASE_URL = import.meta.env.VITE_API_RECOMENDACAO_URL ?? "http://localhost:8000";

export class ErroApiRecomendacao extends Error {}

export async function resolverCep(cep: string): Promise<string | null> {
  const resp = await fetch(`${BASE_URL}/cep/${encodeURIComponent(cep)}`);
  if (resp.status === 404) return null;
  if (!resp.ok) throw new ErroApiRecomendacao(`Falha ao consultar CEP (HTTP ${resp.status})`);
  const dados = (await resp.json()) as { bairro: string };
  return dados.bairro;
}

interface RecomendacaoEscolaApi {
  esc_codigo: string;
  nome: string;
  endereco: string | null;
  bairro: string;
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

export async function buscarPorBairro(
  bairro: string,
  limite = 8,
): Promise<RecomendacaoEscola[]> {
  const resp = await fetch(`${BASE_URL}/recomendacoes?limite=${limite}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enderecos: [{ tipo: "Moradia", bairro }],
    }),
  });
  if (!resp.ok) {
    throw new ErroApiRecomendacao(`Falha ao buscar recomendações (HTTP ${resp.status})`);
  }
  const dados = (await resp.json()) as RecomendacaoEscolaApi[];
  return dados.map(mapearResposta);
}
