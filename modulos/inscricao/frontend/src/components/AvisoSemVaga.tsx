/** Estado vazio das telas 6-9: elas dependem da 1ª escolha do passo 3, que não
 * existe se a busca do passo 2 nunca rodou (ex.: pulando passos pelo painel de
 * teste). Melhor dizer isso do que mostrar uma vaga inventada. */
export function AvisoSemVaga({ onVoltarParaEscolhas }: { onVoltarParaEscolhas: () => void }) {
  return (
    <div className="tela-conteudo">
      <p className="lista-vazia">
        Ainda não há uma creche escolhida para exibir o match. Faça a busca e escolha suas creches
        para continuar.
      </p>
      <button type="button" className="botao-continuar" onClick={onVoltarParaEscolhas}>
        Ir para minhas escolhas
      </button>
    </div>
  );
}
