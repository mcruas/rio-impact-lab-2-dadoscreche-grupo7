interface Opcao<T extends string> {
  valor: T;
  rotulo: string;
  icone: string;
}

interface SegmentedToggleProps<T extends string> {
  opcoes: Opcao<T>[];
  valor: T;
  onSelecionar: (valor: T) => void;
}

export function SegmentedToggle<T extends string>({ opcoes, valor, onSelecionar }: SegmentedToggleProps<T>) {
  return (
    <div className="segmentado">
      {opcoes.map((opcao) => (
        <button
          key={opcao.valor}
          type="button"
          className={`segmentado-item ${valor === opcao.valor ? "segmentado-item--ativo" : ""}`}
          onClick={() => onSelecionar(opcao.valor)}
          aria-pressed={valor === opcao.valor}
        >
          <span aria-hidden="true">{opcao.icone}</span>
          {opcao.rotulo}
        </button>
      ))}
    </div>
  );
}
