import { AvisoSemVaga } from "../components/AvisoSemVaga";
import { CardVaga } from "../components/CardVaga";
import { MatchHeader } from "../components/MatchHeader";
import type { DadosInscricao } from "../types";
import { crecheDoMatch, faixaEtaria } from "../utils/creches";
import { formatarDistancia } from "../utils/distancia";

interface StepProps {
  dados: DadosInscricao;
  onVoltar: () => void;
  onContinuar: () => void;
  onVerEscolhas: () => void;
}

const AJUDA =
  "O match é a vaga que o sistema separou para sua criança, entre as creches que você escolheu. " +
  "Ela fica reservada até o fim do prazo de confirmação.";

/** Tela 6 — "Match encontrado". Não simula o motor de match: mostra a 1ª
 * escolha da família (passo 3) como a vaga encontrada, e justifica o match
 * com o que a própria família preencheu. */
export function Step6Match({ dados, onVoltar, onContinuar, onVerEscolhas }: StepProps) {
  const creche = crecheDoMatch(dados);
  const faixa = faixaEtaria(dados.dataNascimento);

  const motivos = [
    "Uma das escolas que você escolheu",
    faixa ? `Atende à idade da criança (${faixa})` : "Atende à idade da criança",
    dados.turno ? `Atende ao turno escolhido (${dados.turno})` : "Atende ao turno escolhido",
    creche && creche.distanciaKm > 0
      ? `Fica a ${formatarDistancia(creche.distanciaKm)} do endereço informado`
      : "Compatível com sua localização",
  ];

  return (
    <section className="tela">
      <MatchHeader titulo="Match encontrado" onVoltar={onVoltar} ajuda={AJUDA} />

      {creche === null ? (
        <AvisoSemVaga onVoltarParaEscolhas={onVerEscolhas} />
      ) : (
        <>
          <div className="tela-conteudo">
            <div className="match-centralizado">
              <span className="match-check" aria-hidden="true">
                ✓
              </span>
              <h1 className="tela-titulo">Encontramos uma vaga para sua criança!</h1>
              <p className="tela-subtitulo">Estamos muito felizes! 💙</p>
            </div>

            <div className="tela-corpo">
              <CardVaga creche={creche} faixa={faixa} turno={dados.turno} selo="Sua 1ª escolha" />

              <div className="match-motivos">
                <strong>Por que essa vaga combina com você?</strong>
                <ul>
                  {motivos.map((motivo) => (
                    <li key={motivo}>
                      <span className="motivo-check" aria-hidden="true">
                        ✓
                      </span>
                      {motivo}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="caixa-aviso caixa-aviso--prazo">
                <span aria-hidden="true">⏱️</span>
                <div>
                  <strong>Prazo para confirmar</strong>
                  <p>Você tem 3 dias úteis para confirmar essa vaga.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="tela-rodape">
            <button type="button" className="botao-continuar" onClick={onContinuar}>
              Quero essa vaga
            </button>
            <button type="button" className="modal-manter" onClick={onVerEscolhas}>
              Ver minhas escolhas
            </button>
          </div>
        </>
      )}
    </section>
  );
}
