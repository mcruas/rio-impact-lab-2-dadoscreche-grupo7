# Deploy — Match Creche (ao vivo)

- **Site**: https://inscricao-frontend-production.up.railway.app
- **Backend**: https://inscricao-backend-production-3e24.up.railway.app

Tudo hospedado no Railway (projeto `grupo7-inscricao`): 1 banco Postgres + 2
serviços (backend e frontend). Nada em Vercel.

## O que foi feito nesta rodada

- **Persistência real do módulo Inscrição.** `POST /inscricoes` e
  `GET /inscricoes/{cpf}` saíram de stub e passaram a gravar/ler de um
  Postgres de verdade (Railway).
- **Backend unificado.** Os 4 backends de módulo (`inscricao`,
  `recomendacao-escolas`, `match-engine`, `acompanhamento`) continuam sendo
  4 apps FastAPI independentes — só passaram a rodar num único serviço
  Railway, cada um no seu prefixo (`/inscricao`, `/recomendacao-escolas`,
  `/match-engine`, `/acompanhamento`), via `deploy/main.py`. Simplifica o
  deploy sem mudar nenhum código de módulo nem a fronteira de contrato entre
  eles (continuam se chamando só por HTTP).
- **Frontend ligado de verdade.** O passo 4 do formulário agora resolve o
  CEP residencial e chama `POST /inscricoes` de verdade antes de mostrar a
  tela de sucesso — antes disso a tela final era só estática, sem enviar
  nada.
- **Frontend deployado.** Antes só rodava local; agora está no ar junto com
  o backend.
- **Rename**: "Matrícula Carioca" → "Match Creche".

## Como rodar/atualizar

```bash
# Backend unificado (a partir da raiz do repo)
railway up --service inscricao-backend --detach

# Frontend
railway up modulos/inscricao/frontend --path-as-root --service inscricao-frontend --detach
```

Ver `modulos/inscricao/README.md`, `modulos/inscricao/frontend/README.md` e
`modulos/match-engine/README.md`/`modulos/recomendacao-escolas/README.md`
para detalhe de cada módulo, e `RESUMO_IMPACTO.md` pra a síntese de impacto.
