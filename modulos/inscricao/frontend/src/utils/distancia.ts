// Formatação de distância para a família ler.
//
// Antes o cálculo era por centróide de bairro e nunca dava menos de algumas centenas
// de metros, então `toFixed(1)` bastava. Agora a distância é calculada a partir do CEP
// e creches vizinhas aparecem a 20-40 m — com `toFixed(1)` isso virava "0.0 km de
// você", que lê como bug. Abaixo de 1 km mostramos metros.
export function formatarDistancia(km: number): string {
  if (km < 1) {
    const metros = Math.round(km * 1000);
    // Arredondar 0,004 km para "0 m" também lê mal; o piso é 10 m.
    return `${Math.max(metros, 10)} m`;
  }
  return `${km.toFixed(1).replace(".", ",")} km`;
}
