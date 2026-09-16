/* UI: Visão Gantt */

const UIGantt = (() => {

  function flatList(paradaId) {
    const arvore = State.arvoreAtividades(paradaId);
    const out = [];
    arvore.forEach(a => {
      out.push({ atividade: a, nivel: 0 });
      (a.subAtividades || []).forEach(s => out.push({ atividade: s, nivel: 1 }));
    });
    return out;
  }

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
    const linhas = flatList(paradaId).filter(l => l.atividade.dataInicio && l.atividade.dataFim);
    if (linhas.length === 0) {
      return `<div class="empty-state">Nenhuma atividade com datas definidas para exibir no Gantt.</div>`;
    }

    let rangeInicio = null, rangeFim = null;
    linhas.forEach(({ atividade: a }) => {
      const ini = new Date(a.dataInicio), fim = new Date(a.dataFim);
      if (!rangeInicio || ini < rangeInicio) rangeInicio = ini;
      if (!rangeFim || fim > rangeFim) rangeFim = fim;
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

    function barraStyle(a) {
      const ini = new Date(a.dataInicio), fim = new Date(a.dataFim);
      const left = (ini - rangeInicio) / msPorPixel;
      const width = Math.max(6, (fim - ini) / msPorPixel);
      return `left:${left}px; width:${width}px;`;
    }

    const linhasHtml = linhas.map(({ atividade: a, nivel }) => `
      <div class="gantt-row" data-id="${a.id}">
        <div class="gantt-row-label ${nivel > 0 ? 'sub' : ''}" title="${escapeHtml(a.nome)}">${nivel > 0 ? '↳ ' : ''}${escapeHtml(a.nome)}</div>
        <div class="gantt-timeline" style="width:${totalWidth}px">
          <div class="gantt-daycols">${daycolsHtml}</div>
          <div class="gantt-bar status-${a.status}" style="${barraStyle(a)}" title="${escapeHtml(a.nome)}: ${formatDateTime(a.dataInicio)} → ${formatDateTime(a.dataFim)} (${formatHoras(a.duracaoHoras)}, ${a.progresso || 0}%)">
            <div class="gantt-bar-progress" style="width:${a.progresso || 0}%"></div>
            <span style="position:relative;">${escapeHtml(a.nome)}</span>
          </div>
        </div>
      </div>
    `).join('');

    return `
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
