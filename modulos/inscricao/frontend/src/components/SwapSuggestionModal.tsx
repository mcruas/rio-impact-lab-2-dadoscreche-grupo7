import { formatarDistancia } from "../utils/distancia";
import type { RecomendacaoEscola } from "../types";
import { CrecheTags } from "./CrecheTags";

interface SwapSuggestionModalProps {
  posicaoAtual: number;
  crecheAtual: RecomendacaoEscola;
  crecheSugerida: RecomendacaoEscola;
  onTrocar: () => void;
  onManter: () => void;
}

export function SwapSuggestionModal({
  posicaoAtual,
  crecheAtual,
  crecheSugerida,
  onTrocar,
  onManter,
}: SwapSuggestionModalProps) {
  return (
    <div className="modal-fundo" role="dialog" aria-modal="true">
      <div className="modal-caixa">
        <button type="button" className="modal-fechar" onClick={onManter} aria-label="Fechar">
          ✕
        </button>

        <p className="modal-titulo">✓ Outra creche pode ser ainda melhor para você!</p>
        <p className="modal-subtitulo">
          Com base na sua rotina e nas suas escolhas, sugerimos uma opção com maior pontuação.
        </p>

        <div className="modal-card-sugerido">
          <span className="modal-card-selo">MAIOR PONTUAÇÃO ⭐</span>
          <div className="modal-card-linha">
            <span className="creche-foto" aria-hidden="true">
              🏫
            </span>
            <div className="creche-info">
              <h3>{crecheSugerida.nome}</h3>
              <p className="creche-distancia">
                {formatarDistancia(crecheSugerida.distanciaKm)} de você • {crecheSugerida.bairro}
              </p>
              <CrecheTags creche={crecheSugerida} />
            </div>
          </div>
          <p className="modal-motivos">{crecheSugerida.rationale.explicacao}</p>
        </div>

        <p className="modal-atual-rotulo">Sua {posicaoAtual}ª escolha atual:</p>
        <div className="modal-card-atual">
          <span className="creche-foto" aria-hidden="true">
            🏫
          </span>
          <div className="creche-info">
            <h3>{crecheAtual.nome}</h3>
            <p className="creche-distancia">
              {formatarDistancia(crecheAtual.distanciaKm)} de você • {crecheAtual.bairro}
            </p>
            <CrecheTags creche={crecheAtual} />
          </div>
        </div>

        <button type="button" className="botao-continuar" onClick={onTrocar}>
          Trocar pela {crecheSugerida.nome}
        </button>
        <button type="button" className="modal-manter" onClick={onManter}>
          Manter minha escolha
        </button>
      </div>
    </div>
  );
}
