import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import type { RecomendacaoEscola } from "../types";
import { CrecheTags } from "./CrecheTags";

interface OrderableSchoolCardProps {
  posicao: number;
  creche: RecomendacaoEscola;
  onRemover: () => void;
}

export function OrderableSchoolCard({ posicao, creche, onRemover }: OrderableSchoolCardProps) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: creche.escCodigo,
  });

  const estilo = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.6 : 1,
  };

  return (
    <article ref={setNodeRef} style={estilo} className="creche-card-ordenavel">
      <button type="button" className="creche-arrastar" {...attributes} {...listeners} aria-label="Arraste para reordenar">
        ⋮⋮
      </button>
      <span className="creche-posicao">{posicao}</span>
      <span className="creche-foto" aria-hidden="true">
        🏫
      </span>
      <div className="creche-info">
        <h3>{creche.nome}</h3>
        <p className="creche-distancia">
          {creche.distanciaKm > 0
            ? `${creche.distanciaKm.toFixed(1)} km de você • ${creche.bairro}`
            : creche.bairro}
        </p>
        <CrecheTags creche={creche} />
      </div>
      <button type="button" className="creche-remover-x" onClick={onRemover} aria-label="Remover esta creche">
        ✕
      </button>
    </article>
  );
}
