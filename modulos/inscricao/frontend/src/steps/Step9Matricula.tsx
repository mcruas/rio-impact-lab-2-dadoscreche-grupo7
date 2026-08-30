import { AvisoSemVaga } from "../components/AvisoSemVaga";
import { CardVaga } from "../components/CardVaga";
import { MatchHeader } from "../components/MatchHeader";
import type { DadosInscricao } from "../types";
import { crecheDoMatch, faixaEtaria } from "../utils/creches";

interface StepProps {
  dados: DadosInscricao;
  onVoltar: () => void;
  onVerComprovante: () => void;
  onVoltarInicio: () => void;
  onVerEscolhas: () => void;
}

const AJUDA =
  "A matrícula está confirmada no sistema. Falta só a família comparecer à unidade escolar " +
  "com os documentos originais dentro do prazo.";

export function Step9Matricula({
  dados,
  onVoltar,
  onVerComprovante,
  onVoltarInicio,
  onVerEscolhas,
}: StepProps) {
  const creche = crecheDoMatch(dados);
  const faixa = faixaEtaria(dados.dataNascimento);

  return (
    <section className="tela">
      <MatchHeader titulo="Matrícula confirmada" onVoltar={onVoltar} ajuda={AJUDA} />

      {creche === null ? (
        <AvisoSemVaga onVoltarParaEscolhas={onVerEscolhas} />
      ) : (
        <>
          <div className="tela-conteudo">
            <div className="match-centralizado">
              <span className="match-check match-check--grande" aria-hidden="true">
                ✓
              </span>
              <h1 className="tela-titulo">Matrícula confirmada!</h1>
              <p className="tela-subtitulo">
                {dados.nomeCrianca.trim() === ""
                  ? "Sua criança está matriculada."
                  : `${dados.nomeCrianca} está matriculada.`}
              </p>
            </div>

            <div className="tela-corpo">
              <CardVaga creche={creche} faixa={faixa} turno={dados.turno} />

              <div className="caixa-aviso caixa-aviso--sucesso">
                <span aria-hidden="true">🧑‍🏫</span>
                <div>
                  <strong>Próximo passo importante</strong>
                  <p className="caixa-aviso-destaque">
                    Compareça à unidade escolar em até 3 dias úteis.
                  </p>
                  <p>Leve os documentos originais e uma cópia.</p>
                  <p>Não é necessário aguardar contato da escola.</p>
                </div>
              </div>

              <div className="endereco-unidade">
                <div>
                  <strong>Endereço da unidade</strong>
                  {/* endereco vem do dataset de escolas (Query D); no fallback de
                      busca por nome ele é nulo — aí só o bairro é conhecido. */}
                  <p>{creche.endereco ?? "Endereço não informado no cadastro da unidade."}</p>
                  {creche.bairro && <p>{creche.bairro} — Rio de Janeiro/RJ</p>}
                </div>
                <span className="endereco-pino" aria-hidden="true">
                  📍
                </span>
              </div>

              <div className="caixa-aviso caixa-aviso--info">
                <span aria-hidden="true">ℹ️</span>
                <div>
                  <strong>Guarde este comprovante</strong>
                  <p>Você também receberá por e-mail e WhatsApp.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="tela-rodape">
            <button type="button" className="botao-continuar" onClick={onVerComprovante}>
              Ver comprovante ⬇
            </button>
            <button type="button" className="modal-manter" onClick={onVoltarInicio}>
              Voltar para o início
            </button>
          </div>
        </>
      )}
    </section>
  );
}
