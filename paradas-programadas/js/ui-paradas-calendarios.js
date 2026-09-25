/* UI: cadastro de Paradas e Calendários */

const UIParadasCalendarios = (() => {

  // ---------------- Paradas ----------------

  function render() {
    renderListaParadas();
    renderListaCalendarios();
    renderSeletorParada();
  }

  function renderSeletorParada() {
    const sel = document.getElementById('seletor-parada');
    const paradas = State.listarParadas();
    const ativa = State.getParadaAtiva();
    if (paradas.length === 0) {
      sel.innerHTML = `<option value="">Nenhuma parada cadastrada</option>`;
      sel.disabled = true;
    } else {
      sel.disabled = false;
      sel.innerHTML = paradas.map(p => `<option value="${p.id}" ${ativa && ativa.id === p.id ? 'selected' : ''}>${escapeHtml(p.nome)}</option>`).join('');
    }
    document.getElementById('parada-ativa-label').textContent = ativa ? `Parada ativa: ${ativa.nome}` : 'Nenhuma parada selecionada';
  }

  function renderListaParadas() {
    const el = document.getElementById('lista-paradas');
    const paradas = State.listarParadas();
    const ativa = State.getParadaAtiva();
    if (paradas.length === 0) {
      el.innerHTML = `<div class="empty-state">Nenhuma parada cadastrada ainda.<br>Clique em "+ Nova Parada" para começar.</div>`;
      return;
    }
    el.innerHTML = paradas.map(p => {
      const cal = State.getCalendario(p.calendarioId);
      const { inicio, fim } = State.faixaDataParada(p.id);
      const qtdAtividades = State.listarAtividadesDaParada(p.id).length;
      return `
      <div class="card ${ativa && ativa.id === p.id ? 'selected' : ''}" data-id="${p.id}">
        <h3>${escapeHtml(p.nome)}</h3>
        <div class="card-meta">${escapeHtml(p.local || 'sem local definido')} · calendário: ${escapeHtml(cal ? cal.nome : '—')}</div>
        <div class="card-desc">${escapeHtml(p.descricao || 'sem descrição')}</div>
        <div class="card-meta">${qtdAtividades} atividade(s) · ${inicio ? formatDate(inicio) : '—'} a ${fim ? formatDate(fim) : '—'}</div>
        <span class="badge badge-${p.status || 'planejada'}">${STATUS_LABELS[p.status] || 'Planejada'}</span>
        <div class="card-actions mt-8">
          <button class="btn btn-secondary btn-small" data-action="ativar">Definir como ativa</button>
          <button class="btn btn-secondary btn-small" data-action="editar">Editar</button>
          <button class="btn btn-danger btn-small" data-action="excluir">Excluir</button>
        </div>
      </div>`;
    }).join('');

    el.querySelectorAll('.card').forEach(card => {
      const id = card.dataset.id;
      card.querySelector('[data-action="ativar"]').addEventListener('click', () => { State.setParadaAtiva(id); });
      card.querySelector('[data-action="editar"]').addEventListener('click', () => abrirFormParada(State.getParada(id)));
      card.querySelector('[data-action="excluir"]').addEventListener('click', () => {
        if (confirm('Excluir esta parada e todas as suas atividades? Esta ação não pode ser desfeita.')) {
          State.excluirParada(id);
          showToast('Parada excluída.');
        }
      });
    });
  }

  function abrirFormParada(parada) {
    const editando = !!parada;
    parada = parada || { id: null, nome: '', descricao: '', local: '', status: 'planejada', calendarioId: null };
    const calendarios = State.listarCalendarios();

    Modal.open(`
      <h3>${editando ? 'Editar Parada' : 'Nova Parada'}</h3>
      <form id="form-parada">
        <div class="form-grid">
          <div class="form-field full">
            <label>Nome da parada *</label>
            <input type="text" name="nome" required value="${escapeHtml(parada.nome)}" placeholder="Ex.: Parada Geral Unidade 2 - 2026">
          </div>
          <div class="form-field">
            <label>Local / Planta</label>
            <input type="text" name="local" value="${escapeHtml(parada.local || '')}">
          </div>
          <div class="form-field">
            <label>Status</label>
            <select name="status">
              ${Object.entries(STATUS_LABELS).map(([k, v]) => `<option value="${k}" ${parada.status === k ? 'selected' : ''}>${v}</option>`).join('')}
            </select>
          </div>
          <div class="form-field full">
            <label>Calendário utilizado *</label>
            <select name="calendarioId" required>
              ${calendarios.map(c => `<option value="${c.id}" ${parada.calendarioId === c.id ? 'selected' : ''}>${escapeHtml(c.nome)}</option>`).join('')}
            </select>
          </div>
          <div class="form-field full">
            <label>Descrição</label>
            <textarea name="descricao">${escapeHtml(parada.descricao || '')}</textarea>
          </div>
        </div>
        <div class="modal-close-row">
          <button type="button" class="btn btn-secondary" id="btn-cancelar">Cancelar</button>
          <button type="submit" class="btn btn-primary">Salvar</button>
        </div>
      </form>
    `, (box) => {
      box.querySelector('#btn-cancelar').addEventListener('click', Modal.close);
      box.querySelector('#form-parada').addEventListener('submit', (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const salvo = State.salvarParada({
          id: parada.id,
          nome: fd.get('nome').trim(),
          local: fd.get('local').trim(),
          status: fd.get('status'),
          calendarioId: fd.get('calendarioId'),
          descricao: fd.get('descricao').trim()
        });
        if (!editando) State.setParadaAtiva(salvo.id);
        Modal.close();
        showToast('Parada salva.');
      });
    });
  }

  // ---------------- Calendários ----------------

  const DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];

  function renderListaCalendarios() {
    const el = document.getElementById('lista-calendarios');
    const calendarios = State.listarCalendarios();
    el.innerHTML = calendarios.map(c => {
      const diasTxt = c.diasUteis.map((v, i) => v ? DIAS_SEMANA[i] : null).filter(Boolean).join(', ');
      const qtdExc = Object.keys(c.excecoes || {}).length;
      return `
      <div class="card" data-id="${c.id}">
        <h3>${escapeHtml(c.nome)}</h3>
        <div class="card-meta">${c.horasPorDia}h/dia produtivas · dias: ${diasTxt || 'nenhum'}</div>
        <div class="card-meta">${qtdExc} exceção(ões) cadastradas</div>
        <div class="card-actions mt-8">
          <button class="btn btn-secondary btn-small" data-action="editar">Editar</button>
          <button class="btn btn-danger btn-small" data-action="excluir">Excluir</button>
        </div>
      </div>`;
    }).join('');

    el.querySelectorAll('.card').forEach(card => {
      const id = card.dataset.id;
      card.querySelector('[data-action="editar"]').addEventListener('click', () => abrirFormCalendario(State.getCalendario(id)));
      card.querySelector('[data-action="excluir"]').addEventListener('click', () => {
        if (confirm('Excluir este calendário?')) State.excluirCalendario(id);
      });
    });
  }

  function abrirFormCalendario(calendario) {
    const editando = !!calendario;
    calendario = calendario ? JSON.parse(JSON.stringify(calendario)) : {
      id: null, nome: '', horasPorDia: 24,
      diasUteis: [true, true, true, true, true, true, true],
      excecoes: {}
    };

    const linhasExcecoes = Object.entries(calendario.excecoes || {});

    Modal.open(`
      <h3>${editando ? 'Editar Calendário' : 'Novo Calendário'}</h3>
      <form id="form-calendario">
        <div class="form-grid">
          <div class="form-field full">
            <label>Nome *</label>
            <input type="text" name="nome" required value="${escapeHtml(calendario.nome)}" placeholder="Ex.: 24h contínuo, Comercial 8h, etc.">
          </div>
          <div class="form-field">
            <label>Horas produtivas por dia (0-24) *</label>
            <input type="number" name="horasPorDia" min="0" max="24" step="0.5" required value="${calendario.horasPorDia}">
          </div>
        </div>
        <fieldset class="mt-8">
          <legend>Dias da semana úteis</legend>
          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            ${DIAS_SEMANA.map((d, i) => `
              <label style="display:flex; align-items:center; gap:4px; font-size:12px;">
                <input type="checkbox" name="dia${i}" ${calendario.diasUteis[i] ? 'checked' : ''}> ${d}
              </label>`).join('')}
          </div>
        </fieldset>
        <fieldset class="mt-8">
          <legend>Exceções (feriados / dias com capacidade diferente)</legend>
          <div id="lista-excecoes">
            ${linhasExcecoes.map(([data, horas]) => linhaExcecaoHtml(data, horas)).join('')}
          </div>
          <button type="button" class="btn btn-secondary btn-small" id="btn-add-excecao">+ Adicionar exceção</button>
        </fieldset>
        <div class="modal-close-row">
          <button type="button" class="btn btn-secondary" id="btn-cancelar">Cancelar</button>
          <button type="submit" class="btn btn-primary">Salvar</button>
        </div>
      </form>
    `, (box) => {
      box.querySelector('#btn-cancelar').addEventListener('click', Modal.close);
      box.querySelector('#btn-add-excecao').addEventListener('click', () => {
        box.querySelector('#lista-excecoes').insertAdjacentHTML('beforeend', linhaExcecaoHtml('', 0));
        wireRemoverExcecao(box);
      });
      wireRemoverExcecao(box);

      box.querySelector('#form-calendario').addEventListener('submit', (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const diasUteis = DIAS_SEMANA.map((_, i) => fd.get(`dia${i}`) === 'on');
        const excecoes = {};
        box.querySelectorAll('.excecao-row').forEach(row => {
          const data = row.querySelector('.exc-data').value;
          const horas = row.querySelector('.exc-horas').value;
          if (data) excecoes[data] = Number(horas) || 0;
        });
        State.salvarCalendario({
          id: calendario.id,
          nome: fd.get('nome').trim(),
          horasPorDia: Number(fd.get('horasPorDia')),
          diasUteis,
          excecoes
        });
        Modal.close();
        showToast('Calendário salvo.');
      });
    });
  }

  function linhaExcecaoHtml(data, horas) {
    return `
      <div class="excecao-row" style="display:grid; grid-template-columns: 1fr 120px 30px; gap:6px; margin-bottom:6px;">
        <input type="date" class="exc-data" value="${data}">
        <input type="number" class="exc-horas" min="0" max="24" step="0.5" value="${horas}" placeholder="horas">
        <button type="button" class="btn btn-danger btn-small btn-remover-excecao">✕</button>
      </div>`;
  }

  function wireRemoverExcecao(box) {
    box.querySelectorAll('.btn-remover-excecao').forEach(btn => {
      btn.onclick = () => btn.closest('.excecao-row').remove();
    });
  }

  return { render, abrirFormParada, abrirFormCalendario };
})();
