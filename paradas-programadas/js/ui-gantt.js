/* UI: Visão Gantt */

const UIGantt = (() => {

  function diasEntre(inicio, fim) {
    const dias = [];
    let cursor = new Date(inicio);
    cursor.setHours(0, 0, 0, 0);
    const limite = new Date(fim);
    limite.setHours(0, 0, 0, 0);
    while (cursor <= limite) {
      dias.push(new Date(cursor));
      cursor = new Date(cursor.getTime() + 86400000);
    }
    return dias;
  }

  function horasEntre(inicio, fim) {
    const horas = [];
    let cursor = new Date(inicio);
    cursor.setMinutes(0, 0, 0);
    const limite = new Date(fim);
    limite.setMinutes(0, 0, 0);
    while (cursor <= limite) {
      horas.push(new Date(cursor));
      cursor = new Date(cursor.getTime() + 3600000);
    }
    return horas;
  }

  /** Cabeçalho de duas linhas (dia agrupador + hora) usado no zoom "Horas". */
  function headerHorasHtml(horas, colWidth) {
    const grupos = [];
    horas.forEach(h => {
      const key = dateKey(h);
      const atual = grupos[grupos.length - 1];
      if (!atual || atual.key !== key) grupos.push({ key, dia: h, qtd: 1 });
      else atual.qtd++;
    });
    const linhaDias = grupos.map(g =>
      `<div class="gantt-header-cell" style="width:${g.qtd * colWidth}px; font-weight:700;">${pad2(g.dia.getDate())}/${pad2(g.dia.getMonth() + 1)}</div>`
    ).join('');
    const linhaHoras = horas.map(h =>
      `<div class="gantt-header-cell gantt-header-hora" style="width:${colWidth}px;">${pad2(h.getHours())}h</div>`
    ).join('');
    return `<div style="display:flex;">${linhaDias}</div><div style="display:flex;">${linhaHoras}</div>`;
  }

  /** Monta o HTML do grid do Gantt para uma parada. Reaproveitado pelo relatório Gantt. */
  function construirHtmlGantt(paradaId, zoom) {
    const linhas = State.listaAchatada(paradaId).filter(a => a.dataInicio && a.dataFim);
    if (linhas.length === 0) {
      return `<div class="empty-state">Nenhuma atividade com datas definidas para exibir no Gantt.</div>`;
    }

    let rangeInicio = null, rangeFim = null;
    linhas.forEach(a => {
      const ini = new Date(a.dataInicio), fim = new Date(a.dataFim);
      if (!rangeInicio || ini < rangeInicio) rangeInicio = ini;
      if (!rangeFim || fim > rangeFim) rangeFim = fim;
      if (a.inicioReal) {
        const iniR = new Date(a.inicioReal);
        const fimR = a.fimReal ? new Date(a.fimReal) : new Date();
        if (iniR < rangeInicio) rangeInicio = iniR;
        if (fimR > rangeFim) rangeFim = fimR;
      }
    });
    rangeInicio = new Date(rangeInicio.getTime() - 43200000); // meio dia de folga
    rangeFim = new Date(rangeFim.getTime() + 43200000);

    const zoomConfig = {
      hora: { granularidade: 'hora', colWidth: 30 },
      dia: { granularidade: 'dia', colWidth: 46 },
      semana: { granularidade: 'dia', colWidth: 20 }
    }[zoom] || { granularidade: 'dia', colWidth: 20 };

    const colWidth = zoomConfig.colWidth;
    const unidades = zoomConfig.granularidade === 'hora' ? horasEntre(rangeInicio, rangeFim) : diasEntre(rangeInicio, rangeFim);
    const hoje = dateKey(new Date());

    const daycolsHtml = unidades.map(u => {
      const dow = u.getDay();
      const classes = ['gantt-daycol'];
      if (dow === 0 || dow === 6) classes.push('weekend');
      if (dateKey(u) === hoje) classes.push('today');
      return `<div class="${classes.join(' ')}" style="width:${colWidth}px"></div>`;
    }).join('');

    const headerHtml = zoomConfig.granularidade === 'hora'
      ? headerHorasHtml(unidades, colWidth)
      : `<div style="display:flex;">${unidades.map(d => {
          const dow = d.getDay();
          let label = '';
          if (zoom === 'dia') label = `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
          else if (dow === 1 || d.getTime() === unidades[0].getTime()) label = `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
          return `<div class="gantt-header-cell" style="width:${colWidth}px">${label}</div>`;
        }).join('')}</div>`;

    const totalWidth = unidades.length * colWidth;
    const msPorPixel = (rangeFim - rangeInicio) / totalWidth;

    function barraStyle(ini, fim) {
      const left = (ini - rangeInicio) / msPorPixel;
      const width = Math.max(6, (fim - ini) / msPorPixel);
      return `left:${left}px; width:${width}px;`;
    }

    function barraRealHtml(a) {
      if (!a.inicioReal) return '';
      const ini = new Date(a.inicioReal);
      const fim = a.fimReal ? new Date(a.fimReal) : new Date();
      const emAndamento = !a.fimReal;
      const titulo = `Real: ${formatDateTime(a.inicioReal)} → ${a.fimReal ? formatDateTime(a.fimReal) : 'em andamento'}`;
      return `<div class="gantt-bar-real ${emAndamento ? 'em-andamento' : ''}" style="${barraStyle(ini, fim)}" title="${escapeHtml(a.nome)} — ${titulo}"></div>`;
    }

    const linhasHtml = linhas.map(a => {
      const nivel = a.nivel;
      const pred = a.predecessoraId ? State.getAtividade(a.predecessoraId) : null;
      const tituloBase = `${escapeHtml(a.nome)}: ${formatDateTime(a.dataInicio)} → ${formatDateTime(a.dataFim)} (${formatHoras(a.duracaoHoras)}, ${a.progresso || 0}%)`;
      const tituloPred = pred ? ` — após ${escapeHtml(pred.nome)}${a.defasagemHoras ? ` +${a.defasagemHoras}h` : ''}` : '';
      return `
      <div class="gantt-row" data-id="${a.id}">
        <div class="gantt-row-label ${nivel > 0 ? 'sub' : ''}" title="${escapeHtml(a.nome)}">${nivel > 0 ? '↳ ' : ''}${pred ? '🔗 ' : ''}${escapeHtml(a.nome)}</div>
        <div class="gantt-timeline" style="width:${totalWidth}px">
          <div class="gantt-daycols">${daycolsHtml}</div>
          <div class="gantt-bar status-${a.status}" style="${barraStyle(new Date(a.dataInicio), new Date(a.dataFim))}" title="${tituloBase}${tituloPred}">
            <div class="gantt-bar-progress" style="width:${a.progresso || 0}%"></div>
            <span style="position:relative;">${escapeHtml(a.nome)}</span>
          </div>
          ${barraRealHtml(a)}
        </div>
      </div>
    `; }).join('');

    return `
      <div class="gantt-legenda">
        <span><i class="gantt-legenda-dot" style="background:#2563eb"></i> Planejado</span>
        <span><i class="gantt-legenda-dot gantt-legenda-real"></i> Real (concluído)</span>
        <span><i class="gantt-legenda-dot gantt-legenda-real em-andamento"></i> Real (em andamento)</span>
      </div>
      <div class="gantt-grid">
        <div class="gantt-row header-row">
          <div class="gantt-row-label">Atividade</div>
          <div class="gantt-timeline" style="width:${totalWidth}px; min-height:0;">
            ${headerHtml}
          </div>
        </div>
        ${linhasHtml}
      </div>
    `;
  }

  function render() {
    const container = document.getElementById('gantt-container');
    const parada = State.getParadaAtiva();
    if (!parada) {
      container.innerHTML = `<div class="empty-state">Selecione uma parada na aba "Paradas".</div>`;
      return;
    }
    const zoom = document.getElementById('gantt-zoom').value;
    container.innerHTML = construirHtmlGantt(parada.id, zoom);
    container.querySelectorAll('.gantt-row[data-id]').forEach(row => {
      row.addEventListener('click', () => UIAtividades.abrirFormAtividade(State.getAtividade(row.dataset.id)));
    });
  }

  return { render, construirHtmlGantt };
})();
