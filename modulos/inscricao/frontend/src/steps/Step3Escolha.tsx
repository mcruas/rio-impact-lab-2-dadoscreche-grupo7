import { useCallback, useEffect, useState } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import { SortableContext, arrayMove, verticalListSortingStrategy } from "@dnd-kit/sortable";
import { MapaCreches } from "../components/MapaCreches";
import { StepShell } from "../components/StepShell";
import { OrderableSchoolCard } from "../components/OrderableSchoolCard";
import { SwapSuggestionModal } from "../components/SwapSuggestionModal";
import { LIMITE_ESCOLHAS, type DadosInscricao, type RecomendacaoEscola } from "../types";
import { buscarCreche } from "../utils/creches";

interface StepProps {
  dados: DadosInscricao;
  atualizar: (patch: Partial<DadosInscricao>) => void;
  onVoltar: () => void;
  onContinuar: () => void;
}

const POSICAO_SUGESTAO = 3; // 3ª escolha, 1-indexado

/** Melhor candidata dos resultados da busca que ainda não está na lista escolhida. */
function melhorAlternativa(dados: DadosInscricao): RecomendacaoEscola | null {
  const foraDaLista = dados.resultadosBusca.filter(
    (creche) => !dados.crechesEscolhidas.includes(creche.escCodigo),
  );
  if (foraDaLista.length === 0) return null;
  return foraDaLista.reduce((melhor, atual) =>
    atual.pontuacaoFinal > melhor.pontuacaoFinal ? atual : melhor,
  );
}

export function Step3Escolha({ dados, atualizar, onVoltar, onContinuar }: StepProps) {
  const [modalAberto, setModalAberto] = useState(false);
  const [modalJaMostrou, setModalJaMostrou] = useState(false);
  const [avisoLimite, setAvisoLimite] = useState<string | null>(null);

  const lista = dados.crechesEscolhidas;
  const alternativa = melhorAlternativa(dados);
  const listaCheia = lista.length >= LIMITE_ESCOLHAS;

  useEffect(() => {
    setModalJaMostrou(false);
  }, [dados.resultadosBusca]);

  useEffect(() => {
    if (modalJaMostrou || lista.length < POSICAO_SUGESTAO || alternativa === null) return;
    const crecheNaPosicao = buscarCreche(dados.resultadosBusca, lista[POSICAO_SUGESTAO - 1]);
    if (alternativa.pontuacaoFinal <= crecheNaPosicao.pontuacaoFinal) return;

    const temporizador = setTimeout(() => {
      setModalAberto(true);
      setModalJaMostrou(true);
    }, 1200);
    return () => clearTimeout(temporizador);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lista, modalJaMostrou, alternativa]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 150, tolerance: 8 } }),
  );

  function onDragEnd(evento: DragEndEvent) {
    const { active, over } = evento;
    if (!over || active.id === over.id) return;
    const indiceAntigo = lista.indexOf(String(active.id));
    const indiceNovo = lista.indexOf(String(over.id));
    atualizar({ crechesEscolhidas: arrayMove(lista, indiceAntigo, indiceNovo) });
  }

  function remover(escCodigo: string) {
    atualizar({ crechesEscolhidas: lista.filter((codigo) => codigo !== escCodigo) });
    // Abriu vaga na lista: o aviso de limite não faz mais sentido.
    setAvisoLimite(null);
  }

  /** Clique num pino do mapa. Só adiciona: tirar da lista é pelo "×" do card,
   * porque remover sem querer, com o dedo num mapa, é fácil demais. */
  const adicionarPeloMapa = useCallback(
    (escCodigo: string) => {
      if (lista.includes(escCodigo)) return;
      if (lista.length >= LIMITE_ESCOLHAS) {
        setAvisoLimite(
          `Você já escolheu ${LIMITE_ESCOLHAS} creches, que é o máximo. ` +
            "Para adicionar essa, remova uma da lista abaixo no “×”.",
        );
        return;
      }
      atualizar({ crechesEscolhidas: [...lista, escCodigo] });
      setAvisoLimite(null);
    },
    [lista, atualizar],
  );

  function trocarPelaSugestao() {
    if (alternativa === null) return;
    const copia = [...lista];
    copia[POSICAO_SUGESTAO - 1] = alternativa.escCodigo;
    atualizar({ crechesEscolhidas: copia });
    setModalAberto(false);
  }

  return (
    <>
      <StepShell
        numero={3}
        total={5}
        titulo="Escolha e ordene até 5 creches"
        onVoltar={onVoltar}
        onContinuar={onContinuar}
        continuarDesabilitado={lista.length === 0}
      >
        <div className="dica-caixa dica-caixa--estrela">
          <span aria-hidden="true">⭐</span>
          <div>
            <strong>Ordene suas preferências</strong>
            <p>Arraste para ordenar de 1 (maior preferência) a 5 (menor preferência).</p>
          </div>
        </div>

        <div className="sugestoes-cabecalho">
          <strong>Sugestões para você</strong>
          <p>
            Encontramos {dados.resultadosBusca.length} creches na região. Já deixamos as{" "}
            {Math.min(LIMITE_ESCOLHAS, dados.resultadosBusca.length)} mais indicadas na sua lista —
            toque num pino cinza do mapa para trocar por outra.
          </p>
        </div>

        <MapaCreches
          creches={dados.resultadosBusca}
          escolhidas={lista}
          latFamilia={dados.latFamilia}
          lonFamilia={dados.lonFamilia}
          onSelecionar={adicionarPeloMapa}
          podeAdicionar={!listaCheia}
        />

        {avisoLimite !== null && (
          <div className="caixa-aviso caixa-aviso--prazo" role="status">
            <span aria-hidden="true">⚠️</span>
            <div>
              <strong>Sua lista já está cheia</strong>
              <p>{avisoLimite}</p>
            </div>
          </div>
        )}

        <p className={`contagem-escolhas ${listaCheia ? "contagem-escolhas--cheia" : ""}`}>
          {lista.length} de {LIMITE_ESCOLHAS} creches escolhidas
        </p>

        {lista.length === 0 ? (
          <p className="lista-vazia">
            Sua lista está vazia — toque num pino do mapa para adicionar uma creche.
          </p>
        ) : (
          <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={onDragEnd}>
            <SortableContext items={lista} strategy={verticalListSortingStrategy}>
              {lista.map((escCodigo, indice) => (
                <OrderableSchoolCard
                  key={escCodigo}
                  posicao={indice + 1}
                  creche={buscarCreche(dados.resultadosBusca, escCodigo)}
                  onRemover={() => remover(escCodigo)}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}

        {lista.length > 0 && <p className="arraste-dica">↕ Arraste para reordenar</p>}
      </StepShell>

      {modalAberto && alternativa !== null && lista.length >= POSICAO_SUGESTAO && (
        <SwapSuggestionModal
          posicaoAtual={POSICAO_SUGESTAO}
          crecheAtual={buscarCreche(dados.resultadosBusca, lista[POSICAO_SUGESTAO - 1])}
          crecheSugerida={alternativa}
          onTrocar={trocarPelaSugestao}
          onManter={() => setModalAberto(false)}
        />
      )}
    </>
  );
}
