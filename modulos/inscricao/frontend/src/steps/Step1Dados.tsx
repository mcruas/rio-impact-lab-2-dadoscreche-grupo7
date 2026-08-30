import { CampoCpf } from "../components/CampoCpf";
import { PillGroup } from "../components/PillGroup";
import { StepShell } from "../components/StepShell";
import type { DadosInscricao, Turno } from "../types";
import { cpfValido } from "../utils/cpf";

interface StepProps {
  dados: DadosInscricao;
  atualizar: (patch: Partial<DadosInscricao>) => void;
  onVoltar: () => void;
  onContinuar: () => void;
}

const OPCOES_TURNO: { valor: Turno; rotulo: string }[] = [
  { valor: "Integral", rotulo: "Integral" },
  { valor: "Parcial", rotulo: "Parcial" },
];

export function Step1Dados({ dados, atualizar, onVoltar, onContinuar }: StepProps) {
  const preenchido =
    dados.nomeCrianca.trim() !== "" &&
    cpfValido(dados.cpfCrianca) &&
    dados.dataNascimento.trim() !== "" &&
    dados.turno !== null &&
    cpfValido(dados.cpfResponsavel) &&
    dados.cepResidencial.trim() !== "";

  return (
    <StepShell
      numero={1}
      total={5}
      titulo="Dados da criança e do responsável"
      onVoltar={onVoltar}
      onContinuar={onContinuar}
      continuarDesabilitado={!preenchido}
    >
      <h2 className="secao-titulo">Dados da criança</h2>

      <label className="campo">
        <span>Nome da criança</span>
        <input
          type="text"
          value={dados.nomeCrianca}
          onChange={(evento) => atualizar({ nomeCrianca: evento.target.value })}
          placeholder="Digite o nome completo"
        />
      </label>

      <CampoCpf
        rotulo="CPF da criança"
        valor={dados.cpfCrianca}
        onAlterar={(cpfCrianca) => atualizar({ cpfCrianca })}
      />

      <label className="campo">
        <span>Data de nascimento</span>
        <input
          type="date"
          value={dados.dataNascimento}
          onChange={(evento) => atualizar({ dataNascimento: evento.target.value })}
        />
      </label>

      <PillGroup
        pergunta="Qual período a criança precisa?"
        opcoes={OPCOES_TURNO}
        valor={dados.turno}
        onSelecionar={(valor) => atualizar({ turno: valor })}
      />

      <h2 className="secao-titulo">Dados do responsável</h2>

      <CampoCpf
        rotulo="CPF do responsável"
        valor={dados.cpfResponsavel}
        onAlterar={(cpfResponsavel) => atualizar({ cpfResponsavel })}
      />

      <h2 className="secao-titulo">Endereço residencial</h2>
      <p className="secao-descricao">Usaremos seu endereço para sugerir creches próximas.</p>

      <label className="campo">
        <span>CEP</span>
        <div className="campo-com-icone">
          <input
            type="text"
            value={dados.cepResidencial}
            onChange={(evento) => atualizar({ cepResidencial: evento.target.value })}
            placeholder="00000-000"
            inputMode="numeric"
          />
          <span aria-hidden="true">📍</span>
        </div>
      </label>
    </StepShell>
  );
}
