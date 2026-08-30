import { useState } from "react";
import { PillGroup } from "../components/PillGroup";
import { StepShell } from "../components/StepShell";
import type { DadosInscricao, RespostaPrioridade } from "../types";

interface StepProps {
  dados: DadosInscricao;
  atualizar: (patch: Partial<DadosInscricao>) => void;
  onVoltar: () => void;
  onFinalizar: () => Promise<void>;
  onContinuar: () => void;
}

const OPCOES_SIM_NAO_NAOSEI: { valor: RespostaPrioridade; rotulo: string }[] = [
  { valor: "Sim", rotulo: "Sim" },
  { valor: "Nao", rotulo: "Não" },
  { valor: "NaoSei", rotulo: "Não sei" },
];

const OPCOES_SIM_NAO: { valor: "Sim" | "Nao"; rotulo: string }[] = [
  { valor: "Sim", rotulo: "Sim" },
  { valor: "Nao", rotulo: "Não" },
];

export function Step4Prioridade({ dados, atualizar, onVoltar, onFinalizar, onContinuar }: StepProps) {
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const preenchido =
    dados.cadUnico !== null &&
    dados.bolsaFamilia !== null &&
    dados.publicoEducacaoEspecial !== null &&
    dados.outraVulnerabilidade !== null;

  async function enviar() {
    setErro(null);
    setEnviando(true);
    try {
      await onFinalizar();
      onContinuar();
    } catch (excecao) {
      setErro(
        excecao instanceof Error
          ? excecao.message
          : "Não conseguimos enviar sua inscrição agora. Tente de novo em instantes.",
      );
    } finally {
      setEnviando(false);
    }
  }

  return (
    <StepShell
      numero={4}
      total={5}
      titulo="Algumas informações podem dar prioridade à sua inscrição."
      subtitulo="Responda com calma. Você poderá comprovar depois, se necessário."
      onVoltar={onVoltar}
      onContinuar={enviar}
      rotuloContinuar={enviando ? "Enviando…" : "Confirmar inscrição"}
      continuarDesabilitado={!preenchido || enviando}
      notaRodape={
        <>
          {erro && <p className="campo-erro">{erro}</p>}
          <p className="nota-seguranca">
            🔒 As informações serão verificadas conforme as regras do processo. Documentos serão
            solicitados posteriormente, se necessário.
          </p>
        </>
      }
    >
      <PillGroup
        icone="🏠"
        pergunta="Sua família possui CadÚnico?"
        opcoes={OPCOES_SIM_NAO_NAOSEI}
        valor={dados.cadUnico}
        onSelecionar={(valor) => atualizar({ cadUnico: valor })}
      />
      <PillGroup
        icone="🪪"
        pergunta="Recebe Bolsa Família?"
        opcoes={OPCOES_SIM_NAO_NAOSEI}
        valor={dados.bolsaFamilia}
        onSelecionar={(valor) => atualizar({ bolsaFamilia: valor })}
      />
      <PillGroup
        icone="♿"
        pergunta="A criança é público-alvo da Educação Especial?"
        opcoes={OPCOES_SIM_NAO}
        valor={dados.publicoEducacaoEspecial}
        onSelecionar={(valor) => atualizar({ publicoEducacaoEspecial: valor })}
      />
      <PillGroup
        icone="🛟"
        pergunta="Existe alguma outra situação de vulnerabilidade prevista no processo?"
        opcoes={OPCOES_SIM_NAO}
        valor={dados.outraVulnerabilidade}
        onSelecionar={(valor) => atualizar({ outraVulnerabilidade: valor })}
      />
    </StepShell>
  );
}
