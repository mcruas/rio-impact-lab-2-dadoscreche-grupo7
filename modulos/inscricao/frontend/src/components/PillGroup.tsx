interface Opcao<T extends string> {
  valor: T;
  rotulo: string;
}

interface PillGroupProps<T extends string> {
  pergunta: string;
  icone?: string;
  opcoes: Opcao<T>[];
  valor: T | null;
  onSelecionar: (valor: T) => void;
}

export function PillGroup<T extends string>({ pergunta, icone, opcoes, valor, onSelecionar }: PillGroupProps<T>) {
  return (
    <div className="pergunta-prioridade">
      <p className="pergunta-prioridade-texto">
        {icone && (
          <span className="pergunta-icone" aria-hidden="true">
            {icone}
          </span>
        )}
        {pergunta}
      </p>
      <div className="pill-group">
        {opcoes.map((opcao) => (
          <button
            key={opcao.valor}
            type="button"
            className={`pill ${valor === opcao.valor ? "pill--selecionada" : ""}`}
            onClick={() => onSelecionar(opcao.valor)}
            aria-pressed={valor === opcao.valor}
          >
            {opcao.rotulo}
          </button>
        ))}
      </div>
    </div>
  );
}
