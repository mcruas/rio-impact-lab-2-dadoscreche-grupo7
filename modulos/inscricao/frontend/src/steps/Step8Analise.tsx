import { useState } from "react";
import { MatchHeader } from "../components/MatchHeader";
import { MatchStepper } from "../components/MatchStepper";
import type { DadosInscricao } from "../types";
import { crecheDoMatch, faixaEtaria } from "../utils/creches";

interface StepProps {
  dados: DadosInscricao;
  onVoltar: () => void;
  onContinuar: () => void;
}

const AJUDA =
  "A equipe da SME confere se os documentos enviados batem com o que foi declarado na " +
  "inscrição. Enquanto isso a vaga continua reservada.";

function formatarData(dataIso: string): string {
  const partes = dataIso.split("-");
  if (partes.length !== 3) return "—";
  const [ano, mes, dia] = partes;
  return `${dia}/${mes}/${ano}`;
}

function vazio(valor: string): string {
  return valor.trim() === "" ? "—" : valor;
}

export function Step8Analise({ dados, onVoltar, onContinuar }: StepProps) {
  const [detalhesAbertos, setDetalhesAbertos] = useState(false);
  const creche = crecheDoMatch(dados);
  const faixa = faixaEtaria(dados.dataNascimento);

  const detalhes: { rotulo: string; valor: string }[] = [
    { rotulo: "Criança", valor: vazio(dados.nomeCrianca) },
    { rotulo: "CPF da criança", valor: vazio(dados.cpfCrianca) },
    {
      rotulo: "Nascimento",
      valor: faixa
        ? `${formatarData(dados.dataNascimento)} · ${faixa}`
        : formatarData(dados.dataNascimento),
    },
    { rotulo: "Turno", valor: dados.turno ?? "—" },
    { rotulo: "Responsável (CPF)", valor: vazio(dados.cpfResponsavel) },
    { rotulo: "Busca (bairro/CEP)", valor: vazio(dados.buscaTexto) },
    { rotulo: "Creche do match", valor: creche?.nome ?? "—" },
    {
      rotulo: "Entrega dos documentos",
      valor:
        dados.envioDocumentos === "aplicativo"
          ? "Pelo aplicativo"
          : dados.envioDocumentos === "presencial"
            ? "Presencial, na escola"
            : "—",
    },
  ];

  return (
    <section className="tela">
      <MatchHeader titulo="Em análise" onVoltar={onVoltar} ajuda={AJUDA} />
      <MatchStepper atual={3} />

      <div className="tela-conteudo">
        <div className="match-centralizado">
          <span className="analise-icone" aria-hidden="true">
            🗂️
          </span>
          <h1 className="tela-titulo">Documentos em análise</h1>
          <p className="tela-subtitulo">
            Recebemos seus documentos e nossa equipe está analisando as informações.
          </p>
        </div>

        <div className="tela-corpo">
          <div className="caixa-aviso caixa-aviso--info">
            <span aria-hidden="true">⏱️</span>
            <div>
              <strong>Prazo estimado</strong>
              <p>Até 3 dias úteis para concluir a análise.</p>
            </div>
          </div>

          <div className="caixa-aviso caixa-aviso--info">
            <span aria-hidden="true">🔔</span>
            <div>
              <strong>Acompanhe sua inscrição</strong>
              <p>Você será avisado por SMS, e-mail ou WhatsApp sobre o resultado da análise.</p>
            </div>
          </div>

          <button
            type="button"
            className="opcao-envio opcao-envio--secundaria"
            onClick={() => setDetalhesAbertos((aberto) => !aberto)}
            aria-expanded={detalhesAbertos}
          >
            <span className="opcao-envio-texto">
              <strong>Ver detalhes da inscrição</strong>
            </span>
            <span className="opcao-envio-seta" aria-hidden="true">
              {detalhesAbertos ? "⌄" : "›"}
            </span>
          </button>

          {detalhesAbertos && (
            <dl className="detalhes-inscricao">
              {detalhes.map((item) => (
                <div key={item.rotulo}>
                  <dt>{item.rotulo}</dt>
                  <dd>{item.valor}</dd>
                </div>
              ))}
            </dl>
          )}
        </div>
      </div>

      <div className="tela-rodape">
        <button type="button" className="botao-continuar" onClick={onContinuar}>
          Ver resultado da análise
        </button>
        <p className="nota-seguranca">
          Protótipo: no sistema real esta tela espera o resultado e avisa a família por SMS, e-mail
          ou WhatsApp.
        </p>
      </div>
    </section>
  );
}
