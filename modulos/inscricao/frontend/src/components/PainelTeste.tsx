const PASSOS = [1, 2, 3, 4, 5];

interface PainelTesteProps {
  passoAtual: number;
  onPreencher: () => void;
  onIrPara: (passo: number) => void;
}

// Ferramenta só de teste/QA — não faz parte do design da Tela 1. Preenche
// tudo com dados de exemplo (DADOS_EXEMPLO, em data/mockCreches.ts) e deixa
// pular direto pra qualquer passo, sem precisar clicar "Continuar" 5 vezes.
export function PainelTeste({ passoAtual, onPreencher, onIrPara }: PainelTesteProps) {
  return (
    <div className="painel-teste">
      <button type="button" className="painel-teste-preencher" onClick={onPreencher}>
        🧪 Preencher com dados de teste
      </button>
      <div className="painel-teste-passos">
        <span>Ir direto para:</span>
        {PASSOS.map((passo) => (
          <button
            key={passo}
            type="button"
            className={passo === passoAtual ? "painel-teste-passo--ativo" : ""}
            onClick={() => onIrPara(passo)}
          >
            {passo}
          </button>
        ))}
      </div>
    </div>
  );
}
