// Mapa das creches recomendadas, com o pino da família por cima.
//
// Leaflet + OpenStreetMap: é a única opção sem chave de API nem cobrança — Mapbox e
// Google exigiriam credencial, o que não dá para commitar num protótipo.
//
// Nem toda creche tem coordenada: o fallback de "buscar por creche" (nome) é mockado
// e vem sem lat/long (ver data/mockCreches.ts), e a família só tem coordenada quando
// buscou por CEP conhecido. O componente trata os dois casos em vez de quebrar.

import { useEffect, useMemo, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import type { RecomendacaoEscola } from "../types";
import { formatarDistancia } from "../utils/distancia";

interface MapaCrechesProps {
  creches: RecomendacaoEscola[];
  /** escCodigo na ordem de preferência — define o número do pino e o destaque. */
  escolhidas: string[];
  latFamilia: number | null;
  lonFamilia: number | null;
  /** Chamado ao clicar num pino de creche, para a lista destacar a mesma. */
  onSelecionar?: (escCodigo: string) => void;
}

// Pino numerado desenhado em SVG inline — evita depender dos PNG do Leaflet, que
// quebram com bundler (o CSS aponta para caminhos relativos que o Vite não resolve).
function pinoNumerado(rotulo: string, escolhida: boolean): L.DivIcon {
  const cor = escolhida ? "#1d4ed8" : "#94a3b8";
  return L.divIcon({
    className: "mapa-pino",
    html: `<svg width="30" height="40" viewBox="0 0 30 40" xmlns="http://www.w3.org/2000/svg">
      <path d="M15 0C6.7 0 0 6.7 0 15c0 11 15 25 15 25s15-14 15-25C30 6.7 23.3 0 15 0z" fill="${cor}"/>
      <circle cx="15" cy="15" r="10" fill="#fff"/>
      <text x="15" y="19.5" text-anchor="middle" font-size="12" font-weight="700" fill="${cor}"
        font-family="system-ui, sans-serif">${rotulo}</text>
    </svg>`,
    iconSize: [30, 40],
    iconAnchor: [15, 40],
    popupAnchor: [0, -38],
  });
}

function pinoCasa(): L.DivIcon {
  return L.divIcon({
    className: "mapa-pino",
    html: `<svg width="34" height="34" viewBox="0 0 34 34" xmlns="http://www.w3.org/2000/svg">
      <circle cx="17" cy="17" r="15" fill="#059669" stroke="#fff" stroke-width="3"/>
      <text x="17" y="23" text-anchor="middle" font-size="16">🏠</text>
    </svg>`,
    iconSize: [34, 34],
    iconAnchor: [17, 17],
    popupAnchor: [0, -18],
  });
}

function escaparHtml(texto: string): string {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

/** Largura do pino em pixels: abaixo disso dois pinos se encavalam na tela. */
const COLISAO_PX = 30;
/** Raio, em pixels, do circulozinho em que abrimos os pinos empilhados. */
const RAIO_ESPALHAMENTO_PX = 20;

/**
 * Afasta os pinos que cairiam praticamente no mesmo ponto da tela.
 *
 * Com a distância vindo do CEP é comum o topo do ranking ser um bloco de creches a
 * 20-40 m umas das outras (ex.: Raio de Sol, EDI Borel e CIEP Magarinos, todas no
 * Borel). Sem isso elas viram uma pilha só e os números da ordem de preferência ficam
 * ilegíveis.
 *
 * A colisão é medida **em pixels**, não em graus: o que importa é o tamanho do pino na
 * tela no zoom atual, e uma grade em graus erra nos dois sentidos (separa demais quando
 * o mapa está afastado, de menos quando está perto). Por isso a função recebe o mapa —
 * ela só funciona depois que a view já está posicionada.
 */
function espalharColisoes(
  mapa: L.Map,
  itens: { lat: number; lon: number }[],
): { lat: number; lon: number }[] {
  const pixels = itens.map((item) => mapa.latLngToLayerPoint(L.latLng(item.lat, item.lon)));

  // Agrupamento guloso: cada ponto entra no primeiro grupo cujo primeiro membro
  // está a menos de COLISAO_PX dele.
  const grupos: number[][] = [];
  pixels.forEach((pixel, indice) => {
    const grupo = grupos.find((g) => pixels[g[0]].distanceTo(pixel) < COLISAO_PX);
    if (grupo) grupo.push(indice);
    else grupos.push([indice]);
  });

  const saida = itens.map((item) => ({ ...item }));
  for (const indices of grupos) {
    if (indices.length < 2) continue;
    indices.forEach((indice, i) => {
      const angulo = (2 * Math.PI * i) / indices.length;
      const deslocado = L.point(
        pixels[indice].x + RAIO_ESPALHAMENTO_PX * Math.cos(angulo),
        pixels[indice].y + RAIO_ESPALHAMENTO_PX * Math.sin(angulo),
      );
      const latlng = mapa.layerPointToLatLng(deslocado);
      saida[indice] = { lat: latlng.lat, lon: latlng.lng };
    });
  }
  return saida;
}

export function MapaCreches({
  creches,
  escolhidas,
  latFamilia,
  lonFamilia,
  onSelecionar,
}: MapaCrechesProps) {
  const container = useRef<HTMLDivElement>(null);
  const mapa = useRef<L.Map | null>(null);
  const camadaPinos = useRef<L.LayerGroup | null>(null);

  const comCoordenada = useMemo(
    () => creches.filter((c) => c.latitude !== null && c.longitude !== null),
    [creches],
  );

  // Cria o mapa uma vez. O Leaflet é imperativo e guarda estado no nó do DOM, então
  // ele vive numa ref e só os pinos são recriados quando os dados mudam.
  useEffect(() => {
    if (container.current === null || mapa.current !== null) return;
    mapa.current = L.map(container.current, { scrollWheelZoom: false });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(mapa.current);
    camadaPinos.current = L.layerGroup().addTo(mapa.current);
    return () => {
      mapa.current?.remove();
      mapa.current = null;
      camadaPinos.current = null;
    };
  }, []);

  useEffect(() => {
    const m = mapa.current;
    const camada = camadaPinos.current;
    if (m === null || camada === null) return;

    camada.clearLayers();
    // O container só ganha altura depois do primeiro paint dentro do StepShell; sem
    // isso o Leaflet acha que o mapa tem 0px e projeta tudo errado.
    m.invalidateSize();

    // 1. Enquadrar primeiro. espalharColisoes() mede colisão em pixels, então precisa
    //    do zoom já definido — e `animate: false` garante que a projeção vale agora,
    //    não no fim de uma animação.
    const brutos = comCoordenada.map((c) => L.latLng(c.latitude as number, c.longitude as number));
    if (latFamilia !== null && lonFamilia !== null) brutos.push(L.latLng(latFamilia, lonFamilia));

    if (brutos.length === 1) {
      m.setView(brutos[0], 17, { animate: false });
    } else if (brutos.length > 1) {
      m.fitBounds(L.latLngBounds(brutos), { padding: [36, 36], maxZoom: 18, animate: false });
    } else {
      m.setView([-22.9068, -43.1729], 11, { animate: false }); // Rio inteiro
    }

    // 2. Agora sim, espalhar os pinos empilhados e desenhar.
    const posicoes = espalharColisoes(
      m,
      comCoordenada.map((c) => ({ lat: c.latitude as number, lon: c.longitude as number })),
    );

    comCoordenada.forEach((creche, indice) => {
      const posicao = escolhidas.indexOf(creche.escCodigo);
      const escolhida = posicao !== -1;
      const rotulo = escolhida ? String(posicao + 1) : "•";
      const marcador = L.marker([posicoes[indice].lat, posicoes[indice].lon], {
        icon: pinoNumerado(rotulo, escolhida),
        title: creche.nome,
        // Pinos da lista por cima dos demais, para o número nunca ficar escondido.
        zIndexOffset: escolhida ? 1000 - posicao : 0,
      });
      marcador.bindPopup(
        `<strong>${escaparHtml(creche.nome)}</strong><br/>` +
          `${escaparHtml(creche.bairro)}<br/>` +
          formatarDistancia(creche.distanciaKm) +
          (escolhida ? `<br/><em>${posicao + 1}ª da sua lista</em>` : ""),
      );
      if (onSelecionar) marcador.on("click", () => onSelecionar(creche.escCodigo));
      marcador.addTo(camada);
    });

    if (latFamilia !== null && lonFamilia !== null) {
      // Fica atrás das creches de propósito: o pino da casa não é espalhado (tem de
      // marcar o ponto real), então numa vizinhança apertada ele cairia justamente em
      // cima de um pino numerado e esconderia a ordem de preferência.
      L.marker([latFamilia, lonFamilia], {
        icon: pinoCasa(),
        title: "Seu endereço",
        zIndexOffset: -1000,
      })
        .bindPopup("<strong>Seu endereço</strong><br/>Origem do cálculo de distância.")
        .addTo(camada);
    }
  }, [comCoordenada, escolhidas, latFamilia, lonFamilia, onSelecionar]);

  if (comCoordenada.length === 0) {
    return (
      <div className="mapa-vazio">
        Este resultado não tem localização para mostrar no mapa. Busque por bairro ou CEP para
        ver as creches posicionadas.
      </div>
    );
  }

  return (
    <div className="mapa-bloco">
      <div ref={container} className="mapa-container" role="application" aria-label="Mapa das creches recomendadas" />
      <p className="mapa-legenda">
        <span className="mapa-legenda-item"><span className="mapa-bolinha mapa-bolinha--escolhida" /> na sua lista</span>
        <span className="mapa-legenda-item"><span className="mapa-bolinha" /> outras encontradas</span>
        {latFamilia !== null && (
          <span className="mapa-legenda-item"><span className="mapa-bolinha mapa-bolinha--casa" /> seu endereço</span>
        )}
      </p>
    </div>
  );
}
