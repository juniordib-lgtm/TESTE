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

    const colWidth = zoom === 'dia' ? 46 : 20;
    const dias = diasEntre(rangeInicio, rangeFim);
    const hoje = dateKey(new Date());

    const daycolsHtml = dias.map(d => {
      const dow = d.getDay();
      const classes = ['gantt-daycol'];
      if (dow === 0 || dow === 6) classes.push('weekend');
      if (dateKey(d) === hoje) classes.push('today');
      return `<div class="${classes.join(' ')}" style="width:${colWidth}px"></div>`;
    }).join('');

    const headerCells = dias.map(d => {
      const dow = d.getDay();
      let label = '';
      if (zoom === 'dia') label = `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
      else if (dow === 1 || d.getTime() === dias[0].getTime()) label = `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}`;
      return `<div class="gantt-header-cell" style="width:${colWidth}px">${label}</div>`;
    }).join('');

    const totalWidth = dias.length * colWidth;
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
            <div style="display:flex;">${headerCells}</div>
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
