import type { RecomendacaoEscola } from "../types";

function rotuloCompatibilidade(indice: number | null): { rotulo: string; classe: string } {
  if (indice === null) return { rotulo: "Sem dado de concorrência", classe: "tag--azul" };
  if (indice >= 0.6) return { rotulo: "Alta concorrência", classe: "tag--laranja" };
  if (indice >= 0.3) return { rotulo: "Concorrência moderada", classe: "tag--azul" };
  return { rotulo: "Baixa concorrência", classe: "tag--verde" };
}

export function CrecheTags({ creche }: { creche: RecomendacaoEscola }) {
  const compatibilidade = rotuloCompatibilidade(creche.indiceConcorrencia);
  return (
    <div className="creche-tags">
      {creche.tipo && <span className="tag tag--azul">{creche.tipo}</span>}
      <span className={`tag ${compatibilidade.classe}`}>{compatibilidade.rotulo}</span>
    </div>
  );
}
