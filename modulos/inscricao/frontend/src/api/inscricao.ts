// Cliente do backend modulos/inscricao (contrato em
// contracts/inscricao.openapi.yaml). URL configurável via env pra funcionar
// tanto local (uvicorn) quanto depois de deploy sem mudar código.

import type { DadosInscricao } from "../types";
import { apenasDigitos } from "../utils/cpf";

const BASE_URL = import.meta.env.VITE_API_INSCRICAO_URL ?? "http://localhost:8003";

export class ErroApiInscricao extends Error {}

export interface InscricaoCriada {
  id: string;
  status: string;
}

export async function criarInscricao(
  dados: DadosInscricao,
  bairroResidencial: string,
): Promise<InscricaoCriada> {
  const resp = await fetch(`${BASE_URL}/inscricoes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      crianca: {
        nome: dados.nomeCrianca,
        cpf: apenasDigitos(dados.cpfCrianca),
        data_nascimento: dados.dataNascimento,
      },
      responsavel: { cpf: apenasDigitos(dados.cpfResponsavel) },
      enderecos_interesse: [
        {
          tipo: "Moradia",
          bairro: bairroResidencial,
          cep: dados.cepResidencial.replace(/\D/g, "") || undefined,
        },
      ],
      turno: dados.turno,
      escolas_escolhidas: dados.crechesEscolhidas,
    }),
  });
  if (!resp.ok) {
    throw new ErroApiInscricao(`Falha ao enviar a inscrição (HTTP ${resp.status})`);
  }
  const json = (await resp.json()) as { id: string; status: string };
  return { id: json.id, status: json.status };
}
