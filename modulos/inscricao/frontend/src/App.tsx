import { useState } from "react";
import { criarInscricao } from "./api/inscricao";
import { resolverCep } from "./api/recomendacaoEscolas";
import { BrandHeader } from "./components/BrandHeader";
import { PainelTeste } from "./components/PainelTeste";
import { DADOS_EXEMPLO } from "./data/mockCreches";
import { Step1Dados } from "./steps/Step1Dados";
import { Step2Busca } from "./steps/Step2Busca";
import { Step3Escolha } from "./steps/Step3Escolha";
import { Step4Prioridade } from "./steps/Step4Prioridade";
import { Step5Confirmacao } from "./steps/Step5Confirmacao";
import { Step6Match } from "./steps/Step6Match";
import { Step7Documentos } from "./steps/Step7Documentos";
import { Step8Analise } from "./steps/Step8Analise";
import { Step9Matricula } from "./steps/Step9Matricula";
import { dadosIniciais, type DadosInscricao } from "./types";

// 1-5: formulário de inscrição. 6-9: fluxo de match (pós-inscrição), que no
// sistema real seria disparado pelo Motor de Match dias depois — aqui é a
// continuação clicável do protótipo, sobre os mesmos dados do formulário.
const TOTAL_TELAS = 9;

function App() {
  const [passo, setPasso] = useState(1);
  const [dados, setDados] = useState<DadosInscricao>(dadosIniciais);

  function atualizar(patch: Partial<DadosInscricao>) {
    setDados((atual) => ({ ...atual, ...patch }));
  }

  function irPara(proximoPasso: number) {
    setPasso(Math.min(Math.max(proximoPasso, 1), TOTAL_TELAS));
  }

  function reiniciar() {
    setDados(dadosIniciais);
    setPasso(1);
  }

  async function finalizarInscricao() {
    const localizacao = await resolverCep(dados.cepResidencial);
    if (localizacao === null) {
      throw new Error("Não encontramos o CEP residencial informado no passo 1.");
    }
    await criarInscricao(dados, localizacao.bairro);
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
        <Step1Dados
          dados={dados}
          atualizar={atualizar}
          onVoltar={() => irPara(passo - 1)}
          onContinuar={() => {
            // O CEP residencial já foi digitado aqui no passo 1 — pedir de novo no
            // passo 2 era pedir a mesma coisa duas vezes. Leva o CEP como busca
            // inicial; a família continua podendo trocar por outro bairro/CEP se
            // quiser creche perto do trabalho, da avó etc.
            const cep = dados.cepResidencial.trim();
            if (cep !== "" && dados.modoBusca === "regiao" && dados.buscaTexto.trim() === "") {
              atualizar({ buscaTexto: cep });
            }
            irPara(2);
          }}
        />
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
        <Step4Prioridade
          dados={dados}
          atualizar={atualizar}
          onVoltar={() => irPara(3)}
          onFinalizar={finalizarInscricao}
          onContinuar={() => irPara(5)}
        />
      )}
      {passo === 5 && (
        <Step5Confirmacao onAcompanhar={() => irPara(6)} onVoltarInicio={reiniciar} />
      )}
      {passo === 6 && (
        <Step6Match
          dados={dados}
          onVoltar={() => irPara(5)}
          onContinuar={() => irPara(7)}
          onVerEscolhas={() => irPara(3)}
        />
      )}
      {passo === 7 && (
        <Step7Documentos
          dados={dados}
          atualizar={atualizar}
          onVoltar={() => irPara(6)}
          onContinuar={() => irPara(8)}
        />
      )}
      {passo === 8 && (
        <Step8Analise dados={dados} onVoltar={() => irPara(7)} onContinuar={() => irPara(9)} />
      )}
      {passo === 9 && (
        <Step9Matricula
          dados={dados}
          onVoltar={() => irPara(8)}
          onVerComprovante={() => window.alert("Protótipo: aqui seria baixado o comprovante de matrícula (PDF).")}
          onVoltarInicio={reiniciar}
          onVerEscolhas={() => irPara(3)}
        />
      )}
    </div>
  );
}

export default App;
