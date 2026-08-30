import { useState } from "react";

interface MatchHeaderProps {
  titulo: string;
  onVoltar: () => void;
  /** Texto do "Ajuda ?" desta tela — cada tela explica a sua etapa. */
  ajuda: string;
}

export function MatchHeader({ titulo, onVoltar, ajuda }: MatchHeaderProps) {
  const [ajudaAberta, setAjudaAberta] = useState(false);

  return (
    <>
      <div className="match-topo">
        <button type="button" className="botao-voltar" onClick={onVoltar} aria-label="Voltar">
          ‹
        </button>
        <span className="match-topo-titulo">{titulo}</span>
        <button
          type="button"
          className="botao-ajuda"
          onClick={() => setAjudaAberta((aberta) => !aberta)}
          aria-expanded={ajudaAberta}
        >
          Ajuda <span aria-hidden="true">?</span>
        </button>
      </div>
      {ajudaAberta && <p className="match-ajuda-caixa">{ajuda}</p>}
    </>
  );
}
