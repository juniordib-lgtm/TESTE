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
    const linhas = State.listaAchatada(parada.id);
    const corpo = linhas.map(a => `
      <tr>
        <td>${'　　'.repeat(a.nivel)}${a.nivel > 0 ? '↳ ' : ''}${escapeHtml(a.nome)}</td>
        <td>${escapeHtml(a.responsavel || '—')}</td>
        <td><span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span></td>
        <td>${formatDateTime(a.dataInicio)}</td>
        <td>${formatDateTime(a.dataFim)}</td>
        <td>${formatHoras(a.duracaoHoras)}</td>
        <td>${a.inicioReal ? formatDateTime(a.inicioReal) : '—'}</td>
        <td>${a.fimReal ? formatDateTime(a.fimReal) : '—'}</td>
        <td>${a.progresso || 0}%</td>
      </tr>`).join('');

    return cabecalho('Relatório Simplificado', parada) + `
      <table style="width:100%; border-collapse:collapse; font-size:12.5px;">
        <thead>
          <tr style="background:#f8fafc;">
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Atividade</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Responsável</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Status</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Início plan.</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Fim plan.</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Duração</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Início real</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Fim real</th>
            <th style="text-align:left; padding:6px; border-bottom:2px solid #e2e8f0;">Progr.</th>
          </tr>
        </thead>
        <tbody>${corpo || `<tr><td colspan="9">Nenhuma atividade cadastrada.</td></tr>`}</tbody>
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
      const pred = a.predecessoraId ? State.getAtividade(a.predecessoraId) : null;
      const sucessoras = State.sucessorasDiretas(a.id);
      return `
        <div style="margin-left:${nivel * 22}px; padding:12px 0; border-bottom:1px solid #e2e8f0;">
          <h4 style="margin-bottom:4px;">${nivel > 0 ? '↳ ' : ''}${escapeHtml(a.nome)} <span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span></h4>
          <p class="text-muted" style="margin:2px 0;">Responsável: ${escapeHtml(a.responsavel || '—')} · Área: ${escapeHtml(a.area || '—')}</p>
          <p class="text-muted" style="margin:2px 0;">Planejado: ${formatDateTime(a.dataInicio)} → ${formatDateTime(a.dataFim)} · Duração: ${formatHoras(a.duracaoHoras)} · Progresso: ${a.progresso || 0}%</p>
          ${pred ? `<p class="text-muted" style="margin:2px 0;">🔗 Predecessora: ${escapeHtml(pred.nome)}${a.defasagemHoras ? ` (+${a.defasagemHoras}h de defasagem)` : ''} — início calculado automaticamente</p>` : ''}
          ${sucessoras.length ? `<p class="text-muted" style="margin:2px 0;">➜ Sucessoras: ${sucessoras.map(s => escapeHtml(s.nome)).join(', ')}</p>` : ''}
          ${a.inicioReal ? `<p class="text-muted" style="margin:2px 0;">Execução real: ${formatDateTime(a.inicioReal)} → ${a.fimReal ? formatDateTime(a.fimReal) : 'em andamento'}${a.fimReal ? ` (${formatHoras(State.duracaoRealHoras(a))})` : ''}</p>` : ''}
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

  // ---------------- Relatório com Imagens ----------------

  function relatorioImagens(parada) {
    const arvore = State.arvoreAtividades(parada.id);
    const comImagem = [];
    const semImagem = [];
    (function coletar(lista, nivel) {
      lista.forEach(a => {
        if ((a.imagens || []).length > 0) comImagem.push({ a, nivel });
        else semImagem.push({ a, nivel });
        coletar(a.subAtividades || [], nivel + 1);
      });
    })(arvore, 0);

    const blocos = comImagem.map(({ a, nivel }) => `
      <div style="margin-left:${nivel * 22}px; padding:14px 0; border-bottom:1px solid #e2e8f0; page-break-inside: avoid;">
        <h4 style="margin-bottom:4px;">${nivel > 0 ? '↳ ' : ''}${escapeHtml(a.nome)} <span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span></h4>
        <p class="text-muted" style="margin:2px 0;">Responsável: ${escapeHtml(a.responsavel || '—')} · Planejado: ${formatDateTime(a.dataInicio)} → ${formatDateTime(a.dataFim)}</p>
        <div class="imagens-grid" style="margin-top:8px;">
          ${a.imagens.map(img => `
            <div style="text-align:center;">
              <div class="imagem-thumb" style="width:170px; height:170px;"><img src="${img.dataUrl}" alt="${escapeHtml(img.nome)}"></div>
              <div class="text-muted" style="font-size:11px; margin-top:2px; max-width:170px;">${escapeHtml(img.nome || '')}</div>
            </div>`).join('')}
        </div>
      </div>
    `).join('');

    const listaSemImagem = semImagem.length
      ? `<p class="text-muted mt-8">Sem imagens anexadas: ${semImagem.map(({ a }) => escapeHtml(a.nome)).join(', ')}.</p>`
      : '';

    return cabecalho('Relatório com Imagens', parada) +
      (comImagem.length ? blocos : '<p>Nenhuma atividade possui imagens anexadas.</p>') +
      listaSemImagem;
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
    document.getElementById('btn-rel-imagens').addEventListener('click', () => exibir(relatorioImagens));
  }

  return { render, wireBotoes };
})();
