/* UI: Visão em Tabela */

const UITabela = (() => {
  const COLUNAS = [
    { key: 'nome', label: 'Atividade' },
    { key: 'tipoLabel', label: 'Tipo' },
    { key: 'responsavel', label: 'Responsável' },
    { key: 'area', label: 'Área' },
    { key: 'statusLabel', label: 'Status' },
    { key: 'dataInicio', label: 'Início' },
    { key: 'dataFim', label: 'Fim' },
    { key: 'duracaoHoras', label: 'Duração' },
    { key: 'progresso', label: 'Progresso' },
    { key: 'qtdRecursos', label: 'Recursos' },
    { key: 'qtdImagens', label: 'Imagens' }
  ];

  let ordenacao = { campo: 'dataInicio', asc: true };
  let filtro = { status: '', busca: '' };

  function linhasBase() {
    const parada = State.getParadaAtiva();
    if (!parada) return [];
    return State.listarAtividadesDaParada(parada.id).map(a => ({
      ...a,
      tipoLabel: a.parentId ? 'Sub-atividade' : 'Atividade',
      statusLabel: STATUS_LABELS[a.status] || a.status,
      qtdRecursos: (a.recursos || []).length,
      qtdImagens: (a.imagens || []).length
    }));
  }

  function aplicarFiltros(linhas) {
    return linhas.filter(l => {
      if (filtro.status && l.status !== filtro.status) return false;
      if (filtro.busca) {
        const alvo = `${l.nome} ${l.responsavel} ${l.area}`.toLowerCase();
        if (!alvo.includes(filtro.busca.toLowerCase())) return false;
      }
      return true;
    });
  }

  function ordenar(linhas) {
    const { campo, asc } = ordenacao;
    return linhas.slice().sort((a, b) => {
      let va = a[campo], vb = b[campo];
      if (campo === 'dataInicio' || campo === 'dataFim') { va = va ? new Date(va).getTime() : 0; vb = vb ? new Date(vb).getTime() : 0; }
      if (typeof va === 'string') va = va.toLowerCase();
      if (typeof vb === 'string') vb = vb.toLowerCase();
      if (va < vb) return asc ? -1 : 1;
      if (va > vb) return asc ? 1 : -1;
      return 0;
    });
  }

  function renderFiltros() {
    const el = document.getElementById('filtros-tabela');
    el.innerHTML = `
      <input type="text" id="filtro-busca" placeholder="Buscar por nome, responsável, área…" value="${escapeHtml(filtro.busca)}">
      <select id="filtro-status">
        <option value="">Todos os status</option>
        ${Object.entries(STATUS_LABELS).map(([k, v]) => `<option value="${k}" ${filtro.status === k ? 'selected' : ''}>${v}</option>`).join('')}
      </select>
    `;
    el.querySelector('#filtro-busca').addEventListener('input', (e) => { filtro.busca = e.target.value; renderTabela(); });
    el.querySelector('#filtro-status').addEventListener('change', (e) => { filtro.status = e.target.value; renderTabela(); });
  }

  function renderTabela() {
    const table = document.getElementById('tabela-atividades');
    const parada = State.getParadaAtiva();

    if (!parada) {
      table.querySelector('thead').innerHTML = '';
      table.querySelector('tbody').innerHTML = `<tr><td>Selecione uma parada na aba "Paradas".</td></tr>`;
      return;
    }

    table.querySelector('thead').innerHTML = `<tr>${COLUNAS.map(c =>
      `<th data-key="${c.key}">${c.label} ${ordenacao.campo === c.key ? (ordenacao.asc ? '▲' : '▼') : ''}</th>`
    ).join('')}</tr>`;

    const linhas = ordenar(aplicarFiltros(linhasBase()));
    const tbody = table.querySelector('tbody');
    if (linhas.length === 0) {
      tbody.innerHTML = `<tr><td colspan="${COLUNAS.length}" class="text-muted">Nenhuma atividade encontrada.</td></tr>`;
    } else {
      tbody.innerHTML = linhas.map(l => `
        <tr data-id="${l.id}" style="cursor:pointer;">
          <td>${l.parentId ? '↳ ' : ''}${escapeHtml(l.nome)}</td>
          <td>${l.tipoLabel}</td>
          <td>${escapeHtml(l.responsavel || '—')}</td>
          <td>${escapeHtml(l.area || '—')}</td>
          <td><span class="badge badge-${l.status}">${l.statusLabel}</span></td>
          <td>${formatDateTime(l.dataInicio)}</td>
          <td>${formatDateTime(l.dataFim)}</td>
          <td>${formatHoras(l.duracaoHoras)}</td>
          <td>${l.progresso || 0}%</td>
          <td>${l.qtdRecursos}</td>
          <td>${l.qtdImagens}</td>
        </tr>`).join('');
    }

    table.querySelectorAll('th[data-key]').forEach(th => {
      th.addEventListener('click', () => {
        const key = th.dataset.key;
        if (ordenacao.campo === key) ordenacao.asc = !ordenacao.asc;
        else ordenacao = { campo: key, asc: true };
        renderTabela();
      });
    });
    tbody.querySelectorAll('tr[data-id]').forEach(tr => {
      tr.addEventListener('click', () => UIAtividades.abrirFormAtividade(State.getAtividade(tr.dataset.id)));
    });
  }

  function render() {
    renderFiltros();
    renderTabela();
  }

  return { render };
})();
