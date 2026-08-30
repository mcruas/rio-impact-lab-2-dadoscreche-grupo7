import type { DadosInscricao, RecomendacaoEscola } from "../types";

/** Resolve um escCodigo da lista escolhida contra os resultados da busca.
 * O placeholder existe porque a lista escolhida e os resultados são dois
 * campos independentes: pular direto pra um passo pelo painel de teste deixa
 * um sem o outro, e a tela não pode quebrar por causa disso. */
export function buscarCreche(
  resultados: RecomendacaoEscola[],
  escCodigo: string,
): RecomendacaoEscola {
  return (
    resultados.find((creche) => creche.escCodigo === escCodigo) ?? {
      escCodigo,
      nome: "(creche não encontrada nos resultados)",
      endereco: null,
      bairro: "",
      latitude: null,
      longitude: null,
      tipo: null,
      distanciaKm: 0,
      origemDistancia: "",
      indiceConcorrencia: null,
      preferida: false,
      pontuacaoFinal: 0,
      rationale: { pontosProximidade: 0, pontosAdequacaoScore: 0, pontosHistorico: 0, explicacao: "" },
    }
  );
}

/** A vaga do match é a 1ª escolha da família (passo 3). Null enquanto não
 * houver nenhuma creche escolhida — aí as telas 6-9 mostram estado vazio em
 * vez de inventar uma vaga. */
export function crecheDoMatch(dados: DadosInscricao): RecomendacaoEscola | null {
  const primeira = dados.crechesEscolhidas[0];
  if (primeira === undefined) return null;
  return buscarCreche(dados.resultadosBusca, primeira);
}

/** Idade completa na data de corte da SME (31/03 do ano corrente), que é o
 * critério de turma do processo — não a idade de hoje. Retorna null se a data
 * de nascimento não estiver preenchida (input type="date" => "AAAA-MM-DD"). */
export function idadeNaDataDeCorte(dataNascimento: string): number | null {
  const partes = dataNascimento.split("-");
  if (partes.length !== 3) return null;
  const [ano, mes, dia] = partes.map(Number);
  if (!Number.isFinite(ano) || !Number.isFinite(mes) || !Number.isFinite(dia)) return null;

  const corte = { ano: new Date().getFullYear(), mes: 3, dia: 31 };
  let idade = corte.ano - ano;
  if (mes > corte.mes || (mes === corte.mes && dia > corte.dia)) idade -= 1;
  return idade < 0 ? null : idade;
}

/** Grupo/turma correspondente à idade. Só de exibição — quem decide a turma é
 * a unidade escolar. */
export function faixaEtaria(dataNascimento: string): string | null {
  const idade = idadeNaDataDeCorte(dataNascimento);
  if (idade === null) return null;
  if (idade === 0) return "Berçário I";
  if (idade === 1) return "Berçário II";
  if (idade === 2) return "Maternal I";
  if (idade === 3) return "Maternal II";
  return "Pré-escola";
}
