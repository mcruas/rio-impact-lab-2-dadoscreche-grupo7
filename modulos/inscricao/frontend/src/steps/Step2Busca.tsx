import { useState } from "react";
import { SegmentedToggle } from "../components/SegmentedToggle";
import { StepShell } from "../components/StepShell";
import { buscarPorBairro, ErroApiRecomendacao, resolverCep } from "../api/recomendacaoEscolas";
import { buscarCrechesPorNome } from "../data/mockCreches";
import { TOTAL_CANDIDATAS, type DadosInscricao, type ModoBusca, type RecomendacaoEscola } from "../types";

interface StepProps {
  dados: DadosInscricao;
  atualizar: (patch: Partial<DadosInscricao>) => void;
  onVoltar: () => void;
  onBuscar: (resultados: RecomendacaoEscola[]) => void;
}

const OPCOES_MODO: { valor: ModoBusca; rotulo: string; icone: string }[] = [
  { valor: "regiao", rotulo: "Buscar por bairro/CEP", icone: "📍" },
  { valor: "creche", rotulo: "Buscar por creche", icone: "🏠" },
];

function pareceCep(texto: string): boolean {
  return /^\d{5}-?\d{3}$/.test(texto.trim());
}

export function Step2Busca({ dados, atualizar, onVoltar, onBuscar }: StepProps) {
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function buscar() {
    setErro(null);

    if (dados.modoBusca === "creche") {
      onBuscar(buscarCrechesPorNome(dados.buscaTexto));
      return;
    }

    setCarregando(true);
    try {
      const texto = dados.buscaTexto.trim();
      let bairro = texto;
      // Guardado para ir junto na busca: com o CEP o backend localiza a família pelo
      // próprio CEP em vez do centróide do bairro, o que muda bastante o ranking
      // (dois CEPs da mesma Tijuca devolvem listas sem nenhuma escola em comum).
      let cep: string | undefined;
      if (pareceCep(texto)) {
        const localizacao = await resolverCep(texto);
        if (localizacao === null) {
          setErro("Não encontramos esse CEP. Confira os números ou tente buscar pelo nome do bairro.");
          setCarregando(false);
          return;
        }
        bairro = localizacao.bairro;
        cep = texto;
        // Guardado para o mapa do passo 3 plotar o pino da família.
        atualizar({ latFamilia: localizacao.latitude, lonFamilia: localizacao.longitude });
      } else {
        // Busca por nome de bairro não tem coordenada: limpa a anterior para o mapa
        // não mostrar uma casa em lugar nenhum.
        atualizar({ latFamilia: null, lonFamilia: null });
      }

      // 20 e não 8: as 5 pré-selecionadas viram só o começo da lista — as outras
      // 15 ficam no mapa do passo 3 para a família trocar clicando no pino.
      const resultados = await buscarPorBairro(bairro, TOTAL_CANDIDATAS, cep);
      if (resultados.length === 0) {
        setErro("Não encontramos creches nessa região. Tente um bairro vizinho.");
        setCarregando(false);
        return;
      }
      onBuscar(resultados);
    } catch (excecao) {
      setErro(
        excecao instanceof ErroApiRecomendacao
          ? excecao.message
          : "Não conseguimos falar com o servidor de recomendação agora. Tente de novo em instantes.",
      );
    } finally {
      setCarregando(false);
    }
  }

  return (
    <StepShell
      numero={2}
      total={5}
      titulo="Encontre sua creche"
      subtitulo="Encontre creches por nome ou região."
      onVoltar={onVoltar}
      onContinuar={buscar}
      rotuloContinuar={carregando ? "Buscando…" : "Buscar creches"}
      continuarDesabilitado={dados.buscaTexto.trim() === "" || carregando}
    >
      <SegmentedToggle
        opcoes={OPCOES_MODO}
        valor={dados.modoBusca}
        onSelecionar={(modoBusca) => atualizar({ modoBusca, buscaTexto: "" })}
      />

      {dados.modoBusca === "creche" ? (
        <label className="campo">
          <span>Buscar por creche</span>
          <span className="campo-ajuda">Digite o nome da creche que deseja buscar.</span>
          <div className="campo-com-icone">
            <input
              type="text"
              value={dados.buscaTexto}
              onChange={(evento) => atualizar({ buscaTexto: evento.target.value })}
              placeholder="Ex.: EDI Recanto da Criança"
            />
            <span aria-hidden="true">🔎</span>
          </div>
        </label>
      ) : (
        <label className="campo">
          <span>Buscar por bairro ou CEP</span>
          <span className="campo-ajuda">
            Digite o bairro ou CEP de onde você quer creche perto — pode ser sua casa, o
            trabalho, a casa de familiares…
          </span>
          <div className="campo-com-icone">
            <input
              type="text"
              value={dados.buscaTexto}
              onChange={(evento) => atualizar({ buscaTexto: evento.target.value })}
              placeholder="Ex.: Campo Grande ou 23050-300"
            />
            <span aria-hidden="true">📍</span>
          </div>
        </label>
      )}

      {erro && <p className="campo-erro">{erro}</p>}

      <div className="dica-caixa">
        <span aria-hidden="true">💡</span>
        <div>
          <strong>Dica</strong>
          <p>
            Vamos mostrar as creches mais próximas no mapa. Você poderá escolher até 5 delas na
            próxima etapa.
          </p>
        </div>
      </div>
    </StepShell>
  );
}
