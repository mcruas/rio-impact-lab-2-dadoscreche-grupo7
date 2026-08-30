// Máscara + validação de CPF (formato e dígitos verificadores). Usado nos
// campos "CPF da criança" e "CPF do responsável" (Step1Dados.tsx).

export function apenasDigitos(valor: string): string {
  return valor.replace(/\D/g, "");
}

export function formatarCpf(valor: string): string {
  const digitos = apenasDigitos(valor).slice(0, 11);
  const partes = [digitos.slice(0, 3), digitos.slice(3, 6), digitos.slice(6, 9)].filter(Boolean);
  let formatado = partes.join(".");
  const verificador = digitos.slice(9, 11);
  if (verificador) formatado += `-${verificador}`;
  return formatado;
}

function calcularDigitoVerificador(base: string): number {
  let soma = 0;
  let peso = base.length + 1;
  for (const digito of base) {
    soma += Number(digito) * peso;
    peso -= 1;
  }
  const resto = soma % 11;
  return resto < 2 ? 0 : 11 - resto;
}

export function cpfValido(valor: string): boolean {
  const cpf = apenasDigitos(valor);
  if (cpf.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(cpf)) return false; // 111.111.111-11 etc. — formato válido, CPF inexistente

  const digito1 = calcularDigitoVerificador(cpf.slice(0, 9));
  const digito2 = calcularDigitoVerificador(cpf.slice(0, 9) + digito1);
  return cpf.slice(9, 11) === `${digito1}${digito2}`;
}
