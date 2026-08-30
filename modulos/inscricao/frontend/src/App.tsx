import { useState } from "react";
import { BrandHeader } from "./components/BrandHeader";
import { PainelTeste } from "./components/PainelTeste";
import { DADOS_EXEMPLO } from "./data/mockCreches";
import { Step1Dados } from "./steps/Step1Dados";
import { Step2Busca } from "./steps/Step2Busca";
import { Step3Escolha } from "./steps/Step3Escolha";
import { Step4Prioridade } from "./steps/Step4Prioridade";
import { Step5Confirmacao } from "./steps/Step5Confirmacao";
import { dadosIniciais, type DadosInscricao } from "./types";

const TOTAL_PASSOS = 5;

function App() {
  const [passo, setPasso] = useState(1);
  const [dados, setDados] = useState<DadosInscricao>(dadosIniciais);

  function atualizar(patch: Partial<DadosInscricao>) {
    setDados((atual) => ({ ...atual, ...patch }));
  }

  function irPara(proximoPasso: number) {
    setPasso(Math.min(Math.max(proximoPasso, 1), TOTAL_PASSOS));
  }

  function reiniciar() {
    setDados(dadosIniciais);
    setPasso(1);
  }

  return (
    <div className="app-shell">
      <BrandHeader />
      <PainelTeste
        passoAtual={passo}
        onPreencher={() => setDados(DADOS_EXEMPLO)}
        onIrPara={irPara}
      />

      {passo === 1 && (
        <Step1Dados dados={dados} atualizar={atualizar} onVoltar={() => irPara(passo - 1)} onContinuar={() => irPara(2)} />
      )}
      {passo === 2 && (
        <Step2Busca
          dados={dados}
          atualizar={atualizar}
          onVoltar={() => irPara(1)}
          onBuscar={(resultados) => {
            atualizar({
              resultadosBusca: resultados,
              crechesEscolhidas: resultados.slice(0, 5).map((creche) => creche.escCodigo),
            });
            irPara(3);
          }}
        />
      )}
      {passo === 3 && (
        <Step3Escolha dados={dados} atualizar={atualizar} onVoltar={() => irPara(2)} onContinuar={() => irPara(4)} />
      )}
      {passo === 4 && (
        <Step4Prioridade dados={dados} atualizar={atualizar} onVoltar={() => irPara(3)} onContinuar={() => irPara(5)} />
      )}
      {passo === 5 && (
        <Step5Confirmacao onAcompanhar={() => window.alert("Protótipo: aqui abriria a Tela 3 (Acompanhamento).")} onVoltarInicio={reiniciar} />
      )}
    </div>
  );
}

export default App;
