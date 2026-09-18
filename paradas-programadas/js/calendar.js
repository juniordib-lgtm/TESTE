/*
 * Motor de calculo de datas/duracao baseado em um perfil de calendario.
 *
 * Um calendario define, para cada dia, quantas horas contam como "tempo
 * produtivo" da parada. Assume-se que a janela produtiva de um dia comeca
 * sempre a partir das 00:00 e vai ate `capacidade` horas depois. Isso e uma
 * simplificacao proposital: para paradas que rodam 24h (capacidade = 24,
 * o mais comum), o resultado e identico ao tempo corrido. Para dias com
 * capacidade reduzida (ex.: feriado com equipe reduzida = 8h) ou dias nao
 * uteis (capacidade = 0), o excedente do dia e simplesmente pulado.
 *
 * calendario = {
 *   horasPorDia: number (0-24),
 *   diasUteis: [dom,seg,ter,qua,qui,sex,sab] booleans,
 *   excecoes: { "YYYY-MM-DD": horasNumero }
 * }
 */

function capacidadeDoDia(date, calendario) {
  const key = dateKey(date);
  if (calendario.excecoes && Object.prototype.hasOwnProperty.call(calendario.excecoes, key)) {
    return Number(calendario.excecoes[key]);
  }
  const dow = date.getDay();
  const util = calendario.diasUteis ? !!calendario.diasUteis[dow] : true;
  return util ? Number(calendario.horasPorDia) : 0;
}

/** Soma `horas` de tempo produtivo a partir de `inicio`, retornando a Data Fim. */
function calcularDataFim(inicio, horas, calendario) {
  if (!inicio || !isFinite(horas) || horas < 0) return null;
  let cursor = new Date(inicio);
  let restante = horas;
  let iter = 0;
  const MAX_ITER = 200000;

  while (restante > 1e-9 && iter < MAX_ITER) {
    iter++;
    const capacidade = capacidadeDoDia(cursor, calendario);
    const horaDoDia = cursor.getHours() + cursor.getMinutes() / 60 + cursor.getSeconds() / 3600;

    if (capacidade <= 0 || horaDoDia >= capacidade) {
      // pula para meia-noite do proximo dia
      const proximo = new Date(cursor);
      proximo.setHours(24, 0, 0, 0);
      cursor = proximo;
      continue;
    }

    const disponivelHoje = capacidade - horaDoDia;
    const consumir = Math.min(restante, disponivelHoje);
    cursor = new Date(cursor.getTime() + consumir * 3600000);
    restante -= consumir;
  }

  return cursor;
}

/** Calcula quantas horas produtivas existem entre `inicio` e `fim`. */
function calcularDuracaoHoras(inicio, fim, calendario) {
  if (!inicio || !fim) return 0;
  let cursor = new Date(inicio);
  const fimDate = new Date(fim);
  if (fimDate <= cursor) return 0;

  let total = 0;
  let iter = 0;
  const MAX_ITER = 200000;

  while (cursor < fimDate && iter < MAX_ITER) {
    iter++;
    const capacidade = capacidadeDoDia(cursor, calendario);
    const horaDoDia = cursor.getHours() + cursor.getMinutes() / 60 + cursor.getSeconds() / 3600;

    const proximaMeiaNoite = new Date(cursor);
    proximaMeiaNoite.setHours(24, 0, 0, 0);
    const fimSegmento = fimDate < proximaMeiaNoite ? fimDate : proximaMeiaNoite;
    const horasNoSegmento = (fimSegmento - cursor) / 3600000;

    if (capacidade > horaDoDia) {
      const contam = Math.min(capacidade - horaDoDia, horasNoSegmento);
      total += Math.max(0, contam);
    }

    cursor = fimSegmento;
  }

  return roundTo(total, 2);
}

/** Calendario padrao: parada rodando 24h por dia, todos os dias, sem excecoes. */
function calendarioPadrao() {
  return {
    id: uid(),
    nome: 'Padrão 24h (todos os dias)',
    horasPorDia: 24,
    diasUteis: [true, true, true, true, true, true, true],
    excecoes: {}
  };
}
