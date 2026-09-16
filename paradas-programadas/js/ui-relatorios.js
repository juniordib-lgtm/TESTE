/* UI: Relatórios (simplificado, completo/detalhado, Gantt) — todos imprimíveis */

const UIRelatorios = (() => {

  function cabecalho(titulo, parada) {
    const s = UIResumo.calcularEstatisticas(parada.id);
    return `
      <div class="report-toolbar">
        <button class="btn btn-primary" id="btn-imprimir">🖨 Imprimir / Salvar PDF</button>
      </div>
      <h2>${escapeHtml(titulo)}</h2>
      <h3 style="font-weight:400; color:#64748b;">${escapeHtml(parada.nome)}</h3>
      <p class="text-muted">Local: ${escapeHtml(parada.local || '—')} · Gerado em ${formatDateTime(new Date())}</p>
      <p class="text-muted">Período: ${s.inicio ? formatDateTime(s.inicio) : '—'} até ${s.fim ? formatDateTime(s.fim) : '—'} · Duração total: ${s.duracaoTotalParadaHoras !== null ? formatHoras(s.duracaoTotalParadaHoras) : '—'} · ${s.total} atividade(s) · progresso médio ${s.progressoMedio}%</p>
      <hr style="margin:14px 0; border:none; border-top:1px solid #e2e8f0;">
    `;
  }

  function wireImprimir(container) {
    const btn = container.querySelector('#btn-imprimir');
    if (btn) btn.addEventListener('click', () => window.print());
  }

  // ---------------- Relatório Simplificado ----------------

  function relatorioSimplificado(parada) {
    const linhas = State.listarAtividadesDaParada(parada.id);
    const corpo = linhas.map(a => `
      <tr>
        <td>${a.parentId ? '↳ ' : ''}${escapeHtml(a.nome)}</td>
        <td>${escapeHtml(a.responsavel || '—')}</td>
        <td><span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span></td>
        <td>${formatDateTime(a.dataInicio)}</td>
        <td>${formatDateTime(a.dataFim)}</td>
        <td>${formatHoras(a.duracaoHoras)}</td>
        <td>${a.progresso || 0}%</td>
      </tr>`).join('');

    return cabecalho('Relatório Simplificado', parada) + `
      <table style="width:100%; border-collapse:collapse; font-size:12.5px;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Atividade</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Responsável</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Status</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Início</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Fim</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Duração</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Progr.</th>
          </tr>
        </thead>
        <tbody>${corpo || `<tr><td colspan="7">Nenhuma atividade cadastrada.</td></tr>`}</tbody>
      </table>
    `;
  }

  // ---------------- Relatório Completo / Detalhado ----------------

  function relatorioCompleto(parada) {
    const arvore = State.arvoreAtividades(parada.id);

    function blocoAtividade(a, nivel) {
      const recursos = a.recursos || [];
      const imagens = a.imagens || [];
      const custo = recursos.reduce((acc, r) => acc + (Number(r.quantidade) || 0) * (Number(r.custoUnitario) || 0), 0);
      return `
        <div style="margin-left:${nivel * 22}px; padding:12px 0; border-bottom:1px solid #e2e8f0;">
          <h4 style="margin-bottom:4px;">${nivel > 0 ? '↳ ' : ''}${escapeHtml(a.nome)} <span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span></h4>
          <p class="text-muted" style="margin:2px 0;">Responsável: ${escapeHtml(a.responsavel || '—')} · Área: ${escapeHtml(a.area || '—')}</p>
          <p class="text-muted" style="margin:2px 0;">Início: ${formatDateTime(a.dataInicio)} · Fim: ${formatDateTime(a.dataFim)} · Duração: ${formatHoras(a.duracaoHoras)} · Progresso: ${a.progresso || 0}%</p>
          ${a.descricao ? `<p style="margin:6px 0;">${escapeHtml(a.descricao)}</p>` : ''}
          ${recursos.length ? `
            <table style="width:100%; border-collapse:collapse; font-size:12px; margin-top:6px;">
              <thead><tr style="background:#f8fafc;">
                <th style="text-align:left; padding:4px; border-bottom:1px solid #e2e8f0;">Recurso</th>
                <th style="text-align:left; padding:4px; border-bottom:1px solid #e2e8f0;">Tipo</th>
                <th style="text-align:left; padding:4px; border-bottom:1px solid #e2e8f0;">Qtd</th>
                <th style="text-align:left; padding:4px; border-bottom:1px solid #e2e8f0;">Unid.</th>
                <th style="text-align:left; padding:4px; border-bottom:1px solid #e2e8f0;">Custo unit.</th>
              </tr></thead>
              <tbody>
                ${recursos.map(r => `<tr>
                  <td style="padding:4px;">${escapeHtml(r.nome || '—')}</td>
                  <td style="padding:4px;">${escapeHtml((TIPOS_RECURSO_LABEL[r.tipo] || r.tipo))}</td>
                  <td style="padding:4px;">${r.quantidade ?? '—'}</td>
                  <td style="padding:4px;">${escapeHtml(r.unidade || '—')}</td>
                  <td style="padding:4px;">${r.custoUnitario ? 'R$ ' + Number(r.custoUnitario).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '—'}</td>
                </tr>`).join('')}
              </tbody>
            </table>
            ${custo > 0 ? `<p class="text-muted" style="margin-top:4px;">Custo estimado dos recursos: R$ ${custo.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</p>` : ''}
          ` : `<p class="text-muted" style="margin-top:6px;">Nenhum recurso cadastrado.</p>`}
          ${imagens.length ? `
            <div class="imagens-grid" style="margin-top:8px;">
              ${imagens.map(img => `<div class="imagem-thumb" style="width:110px; height:110px;"><img src="${img.dataUrl}" alt="${escapeHtml(img.nome)}"></div>`).join('')}
            </div>` : ''}
        </div>
        ${(a.subAtividades || []).map(s => blocoAtividade(s, nivel + 1)).join('')}
      `;
    }

    return cabecalho('Relatório Completo e Detalhado', parada) +
      (arvore.length ? arvore.map(a => blocoAtividade(a, 0)).join('') : '<p>Nenhuma atividade cadastrada.</p>');
  }

  const TIPOS_RECURSO_LABEL = {
    mao_de_obra: 'Mão de obra', equipamento: 'Equipamento', material: 'Material', servico: 'Serviço'
  };

  // ---------------- Relatório Gantt ----------------

  function relatorioGantt(parada) {
    const ganttHtml = UIGantt.construirHtmlGantt(parada.id, 'dia');
    return cabecalho('Relatório Gantt', parada) + `<div class="gantt-container" style="border:none;">${ganttHtml}</div>`;
  }

  // ---------------- Wiring ----------------

  function exibir(gerarFn) {
    const parada = State.getParadaAtiva();
    const el = document.getElementById('relatorio-preview');
    if (!parada) {
      el.innerHTML = `<div class="empty-state">Selecione uma parada na aba "Paradas" antes de gerar um relatório.</div>`;
      return;
    }
    el.innerHTML = gerarFn(parada);
    wireImprimir(el);
  }

  function render() {
    document.getElementById('relatorio-preview').innerHTML = '<p class="text-muted">Escolha um dos relatórios acima para visualizar.</p>';
  }

  function wireBotoes() {
    document.getElementById('btn-rel-simples').addEventListener('click', () => exibir(relatorioSimplificado));
    document.getElementById('btn-rel-completo').addEventListener('click', () => exibir(relatorioCompleto));
    document.getElementById('btn-rel-gantt').addEventListener('click', () => exibir(relatorioGantt));
  }

  return { render, wireBotoes };
})();
