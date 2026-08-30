interface ProgressDotsProps {
  total: number;
  atual: number; // 1-indexado
}

export function ProgressDots({ total, atual }: ProgressDotsProps) {
  return (
    <div className="progresso-dots" role="progressbar" aria-valuenow={atual} aria-valuemin={1} aria-valuemax={total}>
      {Array.from({ length: total }, (_, indice) => {
        const passo = indice + 1;
        const estado = passo < atual ? "concluido" : passo === atual ? "atual" : "pendente";
        return (
          <span key={passo} className={`dot dot--${estado}`}>
            {passo < total && <span className="dot-linha" />}
          </span>
        );
      })}
    </div>
  );
}
