interface StepProps {
  onAcompanhar: () => void;
  onVoltarInicio: () => void;
}

const PROXIMOS_PASSOS = [
  { icone: "💬", texto: "Buscaremos a melhor vaga para sua criança." },
  { icone: "🔔", texto: "Avisaremos quando houver novidades." },
  { icone: "📋", texto: "Se necessário, pediremos os documentos." },
];

export function Step5Confirmacao({ onAcompanhar, onVoltarInicio }: StepProps) {
  return (
    <section className="tela tela-concluida">
      <div className="tela-conteudo">
        <span className="concluida-icone" aria-hidden="true">
          🎉✅🎉
        </span>
        <h1 className="tela-titulo">Inscrição realizada com sucesso!</h1>
        <p className="tela-subtitulo">Sua inscrição foi recebida e está em análise.</p>

        <div className="dica-caixa">
          <span aria-hidden="true">🔔</span>
          <p>
            Você poderá acompanhar tudo pelo celular, usando o CPF da criança ou do
            responsável.
          </p>
        </div>

        <div className="proximos-passos">
          <strong>Próximos passos</strong>
          <ul>
            {PROXIMOS_PASSOS.map((passo) => (
              <li key={passo.texto}>
                <span aria-hidden="true">{passo.icone}</span>
                {passo.texto}
              </li>
            ))}
          </ul>
        </div>

        <button type="button" className="botao-continuar" onClick={onAcompanhar}>
          Acompanhar inscrição
        </button>
        <button type="button" className="modal-manter" onClick={onVoltarInicio}>
          Voltar para o início
        </button>
      </div>
    </section>
  );
}
