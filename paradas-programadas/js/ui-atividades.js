/* UI: cadastro de Atividades / Sub-atividades, com recursos e imagens */

const UIAtividades = (() => {

  const TIPOS_RECURSO = {
    mao_de_obra: 'Mão de obra',
    equipamento: 'Equipamento',
    material: 'Material',
    servico: 'Serviço'
  };

  function render() {
    const el = document.getElementById('lista-atividades');
    const parada = State.getParadaAtiva();
    if (!parada) {
      el.innerHTML = `<div class="empty-state">Selecione ou cadastre uma parada primeiro (aba "Paradas").</div>`;
      return;
    }
    const arvore = State.arvoreAtividades(parada.id);
    if (arvore.length === 0) {
      el.innerHTML = `<div class="empty-state">Nenhuma atividade cadastrada para "${escapeHtml(parada.nome)}".<br>Clique em "+ Nova Atividade" para começar.</div>`;
      return;
    }
    el.innerHTML = arvore.map(a => itemHtml(a, false)).join('');
    wireItens(el);
  }

  function itemHtml(a, isSub) {
    const imgs = (a.imagens || []).length;
    const recs = (a.recursos || []).length;
    const subHtml = (a.subAtividades || []).map(s => itemHtml(s, true)).join('');
    const real = a.inicioReal
      ? (a.fimReal ? `✅ Real: ${formatDateTime(a.inicioReal)} → ${formatDateTime(a.fimReal)}` : `▶ Real: iniciado em ${formatDateTime(a.inicioReal)} (em andamento)`)
      : null;
    return `
      <div class="atividade-item ${isSub ? 'sub' : ''}" data-id="${a.id}">
        <div class="atividade-head">
          <div>
            ${isSub ? '<span class="atividade-sub-label">SUB-ATIVIDADE</span>' : ''}
            <span class="atividade-titulo">${escapeHtml(a.nome)}</span>
            <span class="badge badge-${a.status}">${STATUS_LABELS[a.status]}</span>
          </div>
          <div class="atividade-actions">
            ${!isSub ? `<button class="btn btn-secondary btn-small" data-action="nova-sub">+ Sub-atividade</button>` : ''}
            ${imgs > 0 ? `<button class="btn btn-secondary btn-small" data-action="ver-imagens">🖼 Ver imagens (${imgs})</button>` : ''}
            <button class="btn btn-secondary btn-small" data-action="editar">Editar</button>
            <button class="btn btn-danger btn-small" data-action="excluir">Excluir</button>
          </div>
        </div>
        <div class="atividade-info">
          <span>👤 ${escapeHtml(a.responsavel || '—')}</span>
          <span>🗓 Planejado: ${formatDateTime(a.dataInicio)} → ${formatDateTime(a.dataFim)}</span>
          <span>⏱ ${formatHoras(a.duracaoHoras)}</span>
          <span>🧰 ${recs} recurso(s)</span>
          <span>🖼 ${imgs} imagem(ns)</span>
          <span style="display:flex; align-items:center; gap:6px;">
            <div class="progress-bar"><div style="width:${a.progresso || 0}%"></div></div> ${a.progresso || 0}%
          </span>
        </div>
        ${real ? `<div class="atividade-info"><span>${real}</span></div>` : ''}
      </div>
      ${subHtml}
    `;
  }

  function wireItens(el) {
    el.querySelectorAll('.atividade-item').forEach(item => {
      const id = item.dataset.id;
      const btnSub = item.querySelector('[data-action="nova-sub"]');
      if (btnSub) btnSub.addEventListener('click', () => abrirFormAtividade(null, id));
      const btnImagens = item.querySelector('[data-action="ver-imagens"]');
      if (btnImagens) btnImagens.addEventListener('click', () => {
        const at = State.getAtividade(id);
        UIImagens.abrirGaleria(at.nome, at.imagens);
      });
      item.querySelector('[data-action="editar"]').addEventListener('click', () => abrirFormAtividade(State.getAtividade(id)));
      item.querySelector('[data-action="excluir"]').addEventListener('click', () => {
        if (confirm('Excluir esta atividade (e sub-atividades, se houver)?')) {
          State.excluirAtividade(id);
          showToast('Atividade excluída.');
        }
      });
    });
  }

  function abrirFormAtividade(atividade, parentIdSugerido) {
    const parada = State.getParadaAtiva();
    if (!parada) { showToast('Selecione uma parada primeiro.', true); return; }
    const editando = !!atividade;
    atividade = atividade ? JSON.parse(JSON.stringify(atividade)) : {
      id: null, paradaId: parada.id, parentId: parentIdSugerido || null,
      nome: '', descricao: '', responsavel: '', area: '',
      status: 'planejada', progresso: 0,
      dataInicio: toInputDateTime(new Date()),
      duracaoHoras: 8,
      dataFim: '',
      inicioReal: '', fimReal: '',
      imagens: [], recursos: []
    };
    const calendario = State.calendarioDaAtividade(atividade) || State.getCalendario(parada.calendarioId);

    // normaliza datas para o formato aceito por <input type="datetime-local">
    atividade.dataInicio = toInputDateTime(atividade.dataInicio) || atividade.dataInicio;
    if (atividade.dataFim) {
      atividade.dataFim = toInputDateTime(atividade.dataFim);
    } else {
      const fim = calcularDataFim(fromInputDateTime(atividade.dataInicio) || new Date(atividade.dataInicio), Number(atividade.duracaoHoras) || 0, calendario);
      atividade.dataFim = fim ? toInputDateTime(fim) : '';
    }
    atividade.inicioReal = atividade.inicioReal ? toInputDateTime(atividade.inicioReal) : '';
    atividade.fimReal = atividade.fimReal ? toInputDateTime(atividade.fimReal) : '';

    const opcoesPai = State.listarAtividadesDaParada(parada.id)
      .filter(a => !a.parentId && a.id !== atividade.id);

    let imagensAtual = (atividade.imagens || []).slice();
    let recursosAtual = (atividade.recursos || []).map(r => ({ ...r }));

    Modal.open(`
      <h3>${editando ? 'Editar Atividade' : 'Nova Atividade'}</h3>
      <form id="form-atividade">
        <div class="form-grid">
          <div class="form-field full">
            <label>Nome da atividade *</label>
            <input type="text" name="nome" required value="${escapeHtml(atividade.nome)}">
          </div>
          <div class="form-field full">
            <label>Esta é sub-atividade de:</label>
            <select name="parentId">
              <option value="">— Nenhuma (atividade principal) —</option>
              ${opcoesPai.map(o => `<option value="${o.id}" ${atividade.parentId === o.id ? 'selected' : ''}>${escapeHtml(o.nome)}</option>`).join('')}
            </select>
          </div>
          <div class="form-field">
            <label>Responsável</label>
            <input type="text" name="responsavel" value="${escapeHtml(atividade.responsavel || '')}">
          </div>
          <div class="form-field">
            <label>Área / Disciplina</label>
            <input type="text" name="area" value="${escapeHtml(atividade.area || '')}">
          </div>
          <div class="form-field">
            <label>Status</label>
            <select name="status">
              ${Object.entries(STATUS_LABELS).map(([k, v]) => `<option value="${k}" ${atividade.status === k ? 'selected' : ''}>${v}</option>`).join('')}
            </select>
          </div>
          <div class="form-field">
            <label>Progresso (%)</label>
            <input type="number" name="progresso" min="0" max="100" value="${atividade.progresso || 0}">
          </div>
          <div class="form-field">
            <label>Data/Hora Início *</label>
            <input type="datetime-local" name="dataInicio" required value="${atividade.dataInicio}">
          </div>
          <div class="form-field">
            <label>Duração (horas) *</label>
            <input type="number" name="duracaoHoras" min="0" step="0.5" required value="${atividade.duracaoHoras}">
          </div>
          <div class="form-field full">
            <label>Data/Hora Fim (calculada automaticamente — pode editar para recalcular a duração)</label>
            <input type="datetime-local" name="dataFim" value="${atividade.dataFim}">
          </div>
          <div class="form-field full">
            <label>Descrição</label>
            <textarea name="descricao">${escapeHtml(atividade.descricao || '')}</textarea>
          </div>
        </div>

        <fieldset class="mt-8">
          <legend>Execução real</legend>
          <p class="hint" style="margin:0 0 8px;">Preencha conforme a atividade realmente acontece, para comparar planejado × real. Deixe em branco enquanto não iniciada.</p>
          <div class="form-grid">
            <div class="form-field">
              <label>Início real</label>
              <input type="datetime-local" name="inicioReal" value="${atividade.inicioReal}">
            </div>
            <div class="form-field">
              <label>Fim real</label>
              <input type="datetime-local" name="fimReal" value="${atividade.fimReal}">
            </div>
            <div class="form-field full readonly">
              <label>Duração real (calculada)</label>
              <input type="text" id="duracao-real-display" readonly value="—">
            </div>
          </div>
        </fieldset>

        <fieldset class="mt-8">
          <legend>Recursos</legend>
          <div id="recursos-list" class="recursos-list"></div>
          <button type="button" class="btn btn-secondary btn-small" id="btn-add-recurso">+ Adicionar recurso</button>
        </fieldset>

        <fieldset class="mt-8">
          <legend>Imagens</legend>
          <input type="file" id="input-imagens" accept="image/*" multiple>
          <p class="hint" style="margin:6px 0 0;">Clique em uma miniatura para pré-visualizar em tamanho maior.</p>
          <div id="imagens-grid" class="imagens-grid"></div>
        </fieldset>

        <div class="modal-close-row">
          <button type="button" class="btn btn-secondary" id="btn-cancelar">Cancelar</button>
          <button type="submit" class="btn btn-primary">Salvar</button>
        </div>
      </form>
    `, (box) => {
      const inputInicio = box.querySelector('[name="dataInicio"]');
      const inputDuracao = box.querySelector('[name="duracaoHoras"]');
      const inputFim = box.querySelector('[name="dataFim"]');
      let modoCalculo = 'duracao';

      function recalcularFim() {
        const inicio = fromInputDateTime(inputInicio.value);
        const horas = Number(inputDuracao.value);
        if (!inicio || isNaN(horas)) return;
        const fim = calcularDataFim(inicio, horas, calendario);
        if (fim) inputFim.value = toInputDateTime(fim);
      }
      function recalcularDuracao() {
        const inicio = fromInputDateTime(inputInicio.value);
        const fim = fromInputDateTime(inputFim.value);
        if (!inicio || !fim) return;
        inputDuracao.value = calcularDuracaoHoras(inicio, fim, calendario);
      }

      inputInicio.addEventListener('input', () => { if (modoCalculo === 'duracao') recalcularFim(); else recalcularDuracao(); });
      inputDuracao.addEventListener('input', () => { modoCalculo = 'duracao'; recalcularFim(); });
      inputFim.addEventListener('input', () => { modoCalculo = 'fim'; recalcularDuracao(); });

      // ---- Execução real ----
      const inputInicioReal = box.querySelector('[name="inicioReal"]');
      const inputFimReal = box.querySelector('[name="fimReal"]');
      const duracaoRealDisplay = box.querySelector('#duracao-real-display');
      function recalcularDuracaoReal() {
        const ini = fromInputDateTime(inputInicioReal.value);
        const fim = fromInputDateTime(inputFimReal.value);
        if (ini && fim) {
          duracaoRealDisplay.value = formatHoras(calcularDuracaoHoras(ini, fim, calendario));
        } else if (ini && !fim) {
          duracaoRealDisplay.value = 'em andamento';
        } else {
          duracaoRealDisplay.value = '—';
        }
      }
      inputInicioReal.addEventListener('input', recalcularDuracaoReal);
      inputFimReal.addEventListener('input', recalcularDuracaoReal);
      recalcularDuracaoReal();

      // ---- Recursos ----
      const recursosList = box.querySelector('#recursos-list');
      function renderRecursos() {
        recursosList.innerHTML = recursosAtual.map((r, i) => `
          <div class="recurso-row" data-i="${i}">
            <select class="rec-tipo">
              ${Object.entries(TIPOS_RECURSO).map(([k, v]) => `<option value="${k}" ${r.tipo === k ? 'selected' : ''}>${v}</option>`).join('')}
            </select>
            <input type="text" class="rec-nome" placeholder="Descrição do recurso" value="${escapeHtml(r.nome || '')}">
            <input type="number" class="rec-qtd" placeholder="Qtd" min="0" step="0.01" value="${r.quantidade ?? ''}">
            <input type="text" class="rec-unid" placeholder="Unid." value="${escapeHtml(r.unidade || '')}">
            <input type="number" class="rec-custo" placeholder="Custo unit." min="0" step="0.01" value="${r.custoUnitario ?? ''}">
            <button type="button" class="btn btn-danger btn-small rec-remover">✕</button>
          </div>`).join('') || `<div class="text-muted" style="font-size:12px;">Nenhum recurso adicionado.</div>`;

        recursosList.querySelectorAll('.recurso-row').forEach(row => {
          const i = Number(row.dataset.i);
          row.querySelector('.rec-tipo').addEventListener('change', e => recursosAtual[i].tipo = e.target.value);
          row.querySelector('.rec-nome').addEventListener('input', e => recursosAtual[i].nome = e.target.value);
          row.querySelector('.rec-qtd').addEventListener('input', e => recursosAtual[i].quantidade = e.target.value);
          row.querySelector('.rec-unid').addEventListener('input', e => recursosAtual[i].unidade = e.target.value);
          row.querySelector('.rec-custo').addEventListener('input', e => recursosAtual[i].custoUnitario = e.target.value);
          row.querySelector('.rec-remover').addEventListener('click', () => { recursosAtual.splice(i, 1); renderRecursos(); });
        });
      }
      box.querySelector('#btn-add-recurso').addEventListener('click', () => {
        recursosAtual.push({ id: uid(), tipo: 'mao_de_obra', nome: '', quantidade: 1, unidade: '', custoUnitario: '' });
        renderRecursos();
      });
      renderRecursos();

      // ---- Imagens ----
      const imagensGrid = box.querySelector('#imagens-grid');
      function renderImagens() {
        imagensGrid.innerHTML = imagensAtual.map((img, i) => `
          <div class="imagem-thumb" data-i="${i}">
            <img src="${img.dataUrl}" alt="${escapeHtml(img.nome)}">
            <button type="button" class="img-remover" title="Remover">✕</button>
          </div>`).join('');
        imagensGrid.querySelectorAll('.img-remover').forEach(btn => {
          btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const i = Number(btn.closest('.imagem-thumb').dataset.i);
            imagensAtual.splice(i, 1);
            renderImagens();
          });
        });
        imagensGrid.querySelectorAll('.imagem-thumb img').forEach(imgEl => {
          imgEl.addEventListener('click', () => {
            const i = Number(imgEl.closest('.imagem-thumb').dataset.i);
            UIImagens.abrirGaleria(atividade.nome || 'Imagens', imagensAtual, i);
          });
        });
      }
      box.querySelector('#input-imagens').addEventListener('change', async (e) => {
        const files = Array.from(e.target.files || []);
        for (const file of files) {
          const dataUrl = await fileToDataUrl(file);
          imagensAtual.push({ id: uid(), nome: file.name, tipo: file.type, dataUrl });
        }
        renderImagens();
        e.target.value = '';
      });
      renderImagens();

      box.querySelector('#btn-cancelar').addEventListener('click', Modal.close);
      box.querySelector('#form-atividade').addEventListener('submit', (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const dataInicioDate = fromInputDateTime(fd.get('dataInicio'));
        const dataFimDate = fromInputDateTime(fd.get('dataFim'));
        const inicioRealDate = fromInputDateTime(fd.get('inicioReal'));
        const fimRealDate = fromInputDateTime(fd.get('fimReal'));
        const payload = {
          id: atividade.id,
          paradaId: parada.id,
          parentId: fd.get('parentId') || null,
          nome: fd.get('nome').trim(),
          responsavel: fd.get('responsavel').trim(),
          area: fd.get('area').trim(),
          status: fd.get('status'),
          progresso: Math.max(0, Math.min(100, Number(fd.get('progresso')) || 0)),
          dataInicio: dataInicioDate ? dataInicioDate.toISOString() : null,
          duracaoHoras: Number(fd.get('duracaoHoras')) || 0,
          dataFim: dataFimDate ? dataFimDate.toISOString() : null,
          inicioReal: inicioRealDate ? inicioRealDate.toISOString() : null,
          fimReal: fimRealDate ? fimRealDate.toISOString() : null,
          descricao: fd.get('descricao').trim(),
          ordem: atividade.ordem,
          imagens: imagensAtual,
          recursos: recursosAtual.map(r => ({
            id: r.id || uid(), tipo: r.tipo, nome: r.nome, quantidade: Number(r.quantidade) || 0,
            unidade: r.unidade, custoUnitario: Number(r.custoUnitario) || 0
          }))
        };
        State.salvarAtividade(payload, modoCalculo);
        Modal.close();
        showToast('Atividade salva.');
      });
    });
  }

  return { render, abrirFormAtividade };
})();
