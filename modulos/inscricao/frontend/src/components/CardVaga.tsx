import type { RecomendacaoEscola } from "../types";
import { formatarDistancia } from "../utils/distancia";

interface CardVagaProps {
  creche: RecomendacaoEscola;
  /** Grupo/turma da criança (ex.: "Maternal I"), calculado da data de nascimento. */
  faixa: string | null;
  turno: string | null;
  /** Selo do topo, ex.: "Sua 1ª escolha". Omitido na tela de matrícula. */
  selo?: string;
}

/** Cartão da vaga do match — mesmo card na tela "Match encontrado" e na de
 * "Matrícula confirmada". */
export function CardVaga({ creche, faixa, turno, selo }: CardVagaProps) {
  // distanciaKm = 0 é o fallback da busca por nome (não é distância medida),
  // então nesse caso a linha de distância simplesmente não aparece.
  const temDistancia = creche.distanciaKm > 0;

  return (
    <div className="match-card">
      {selo && <span className="match-card-selo">{selo}</span>}
      <div className="match-card-linha">
        <span className="creche-foto" aria-hidden="true">
          🏫
        </span>
        <div className="creche-info">
          <h3>{creche.nome}</h3>
          {temDistancia && (
            <p className="creche-distancia">
              📍 {formatarDistancia(creche.distanciaKm)} do endereço informado
            </p>
          )}
          {creche.bairro && <p className="creche-distancia">Bairro {creche.bairro}</p>}
          <div className="creche-tags">
            {faixa && <span className="tag tag--azul">{faixa}</span>}
            {turno && <span className="tag tag--verde">{turno}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
