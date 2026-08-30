import type { ReactNode } from "react";
import { ProgressDots } from "./ProgressDots";

interface StepShellProps {
  numero: number;
  total: number;
  titulo: string;
  subtitulo?: string;
  onVoltar: () => void;
  onContinuar: () => void;
  rotuloContinuar?: string;
  continuarDesabilitado?: boolean;
  notaRodape?: ReactNode;
  children: ReactNode;
}

export function StepShell({
  numero,
  total,
  titulo,
  subtitulo,
  onVoltar,
  onContinuar,
  rotuloContinuar = "Continuar",
  continuarDesabilitado = false,
  notaRodape,
  children,
}: StepShellProps) {
  return (
    <section className="tela">
      <div className="tela-topo">
        {numero > 1 ? (
          <button type="button" className="botao-voltar" onClick={onVoltar}>
            ‹ Voltar
          </button>
        ) : (
          <span />
        )}
        <span className="contador-passo">
          {numero} de {total}
        </span>
      </div>

      <ProgressDots total={total} atual={numero} />

      <div className="tela-conteudo">
        <h1 className="tela-titulo">{titulo}</h1>
        {subtitulo && <p className="tela-subtitulo">{subtitulo}</p>}
        <div className="tela-corpo">{children}</div>
      </div>

      <div className="tela-rodape">
        <button
          type="button"
          className="botao-continuar"
          onClick={onContinuar}
          disabled={continuarDesabilitado}
        >
          {rotuloContinuar}
        </button>
        {notaRodape}
      </div>
    </section>
  );
}
