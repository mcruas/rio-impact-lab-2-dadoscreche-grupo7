const ETAPAS = ["Match", "Documentos", "Análise", "Matrícula"];

/** Trilha das 4 etapas do pós-inscrição. É outra numeração, independente dos
 * 5 passos do formulário (ProgressDots) — aqui a família já se inscreveu. */
export function MatchStepper({ atual }: { atual: number }) {
  return (
    <ol className="match-stepper">
      {ETAPAS.map((etapa, indice) => {
        const numero = indice + 1;
        const estado = numero < atual ? "concluida" : numero === atual ? "atual" : "futura";
        return (
          <li key={etapa} className={`match-etapa match-etapa--${estado}`}>
            <div className="match-etapa-linha-caixa">
              {indice > 0 && <span className="match-etapa-linha" aria-hidden="true" />}
              <span className="match-etapa-bolha" aria-hidden="true">
                {estado === "concluida" ? "✓" : numero}
              </span>
              {indice < ETAPAS.length - 1 && <span className="match-etapa-linha" aria-hidden="true" />}
            </div>
            <span className="match-etapa-rotulo" aria-current={estado === "atual" ? "step" : undefined}>
              {etapa}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
