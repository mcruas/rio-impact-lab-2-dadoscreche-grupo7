import { useState } from "react";
import { MatchHeader } from "../components/MatchHeader";
import { MatchStepper } from "../components/MatchStepper";
import type { DadosInscricao, EnvioDocumentos } from "../types";

interface StepProps {
  dados: DadosInscricao;
  atualizar: (patch: Partial<DadosInscricao>) => void;
  onVoltar: () => void;
  onContinuar: () => void;
}

const AJUDA =
  "Os documentos comprovam o que você declarou na inscrição. Você escolhe se envia pelo " +
  "aplicativo ou se leva pessoalmente à escola — as duas formas valem igual.";

// Lista de referência do protótipo, não a lista oficial da SME (quem vai ser
// dono dela é o módulo `documentacao/`). Os itens condicionais vêm das
// respostas do passo 4: só pede comprovação do que a família declarou.
const DOCUMENTOS_BASE = [
  "Certidão de nascimento da criança",
  "CPF da criança",
  "Caderneta de vacinação atualizada",
  "Identidade e CPF do responsável",
  "Comprovante de residência recente",
];

function documentosNecessarios(dados: DadosInscricao): string[] {
  const lista = [...DOCUMENTOS_BASE];
  if (dados.cadUnico === "Sim") lista.push("Folha resumo do CadÚnico");
  if (dados.bolsaFamilia === "Sim") lista.push("Comprovante do Bolsa Família");
  if (dados.publicoEducacaoEspecial === "Sim") lista.push("Laudo ou relatório médico da criança");
  if (dados.outraVulnerabilidade === "Sim")
    lista.push("Documento que comprove a situação declarada");
  return lista;
}

export function Step7Documentos({ dados, atualizar, onVoltar, onContinuar }: StepProps) {
  const [listaAberta, setListaAberta] = useState(false);
  const escolhido = dados.envioDocumentos;

  function escolher(opcao: EnvioDocumentos) {
    atualizar({ envioDocumentos: opcao });
  }

  return (
    <section className="tela">
      <MatchHeader titulo="Confirmar vaga" onVoltar={onVoltar} ajuda={AJUDA} />
      <MatchStepper atual={2} />

      <div className="tela-conteudo">
        <h1 className="tela-titulo">Para confirmar a vaga, precisamos conferir alguns documentos.</h1>
        <p className="tela-subtitulo">
          Você pode enviar os documentos pelo aplicativo ou levar pessoalmente à escola.
        </p>

        <div className="tela-corpo">
          <button
            type="button"
            className={`opcao-envio ${escolhido === "aplicativo" ? "opcao-envio--ativa" : ""}`}
            onClick={() => escolher("aplicativo")}
            aria-pressed={escolhido === "aplicativo"}
          >
            <span className="opcao-envio-icone" aria-hidden="true">
              📱
            </span>
            <span className="opcao-envio-texto">
              <strong>Enviar documentos pelo aplicativo</strong>
              <span>É rápido e seguro.</span>
            </span>
            <span className="opcao-envio-seta" aria-hidden="true">
              ›
            </span>
          </button>

          {escolhido === "aplicativo" && (
            <div className="caixa-aviso caixa-aviso--info">
              <div>
                <strong>Importante:</strong>
                <ul className="lista-marcadores">
                  <li>Os documentos precisam estar legíveis, completos e sem cortes.</li>
                  <li>Fotos escuras, borradas ou com reflexo podem ser recusadas.</li>
                  <li>Arquivos aceitos: JPG, PNG ou PDF (até 10MB).</li>
                </ul>
              </div>
            </div>
          )}

          <div className="divisor-ou">
            <span>ou</span>
          </div>

          <button
            type="button"
            className={`opcao-envio opcao-envio--presencial ${
              escolhido === "presencial" ? "opcao-envio--ativa" : ""
            }`}
            onClick={() => escolher("presencial")}
            aria-pressed={escolhido === "presencial"}
          >
            <span className="opcao-envio-icone" aria-hidden="true">
              🏫
            </span>
            <span className="opcao-envio-texto">
              <strong>Vou à escola levar os documentos</strong>
              <span>
                Para famílias em situação de vulnerabilidade ou que preferem atendimento presencial.
              </span>
            </span>
            <span className="opcao-envio-seta" aria-hidden="true">
              ›
            </span>
          </button>

          <button
            type="button"
            className="opcao-envio opcao-envio--secundaria"
            onClick={() => setListaAberta((aberta) => !aberta)}
            aria-expanded={listaAberta}
          >
            <span className="opcao-envio-icone" aria-hidden="true">
              📋
            </span>
            <span className="opcao-envio-texto">
              <strong>Quais documentos são necessários?</strong>
              <span>Veja a lista completa de documentos exigidos.</span>
            </span>
            <span className="opcao-envio-seta" aria-hidden="true">
              {listaAberta ? "⌄" : "›"}
            </span>
          </button>

          {listaAberta && (
            <div className="lista-documentos">
              <ul className="lista-marcadores">
                {documentosNecessarios(dados).map((documento) => (
                  <li key={documento}>{documento}</li>
                ))}
              </ul>
              <p className="nota-seguranca">
                Lista de referência — a unidade escolar pode solicitar documentos adicionais.
              </p>
            </div>
          )}
        </div>
      </div>

      <div className="tela-rodape">
        <button
          type="button"
          className="botao-continuar"
          onClick={onContinuar}
          disabled={escolhido === null}
        >
          Continuar
        </button>
      </div>
    </section>
  );
}
