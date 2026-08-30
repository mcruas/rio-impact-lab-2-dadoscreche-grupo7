import { apenasDigitos, cpfValido, formatarCpf } from "../utils/cpf";

interface CampoCpfProps {
  rotulo: string;
  valor: string;
  onAlterar: (valorFormatado: string) => void;
}

export function CampoCpf({ rotulo, valor, onAlterar }: CampoCpfProps) {
  const digitos = apenasDigitos(valor);
  const invalido = digitos.length === 11 && !cpfValido(valor);

  return (
    <label className="campo">
      <span>{rotulo}</span>
      <input
        type="text"
        value={valor}
        onChange={(evento) => onAlterar(formatarCpf(evento.target.value))}
        placeholder="000.000.000-00"
        inputMode="numeric"
        maxLength={14}
        aria-invalid={invalido}
        className={invalido ? "campo-input--erro" : ""}
      />
      {invalido && <span className="campo-erro">CPF inválido — confira os números digitados.</span>}
    </label>
  );
}
