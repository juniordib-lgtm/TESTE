/* UI: Resumo (dashboard) */

const UIResumo = (() => {

  function calcularEstatisticas(paradaId) {
    const atividades = State.listarAtividadesDaParada(paradaId);
    const total = atividades.length;
    const porStatus = { planejada: 0, em_andamento: 0, concluida: 0, atrasada: 0 };
    let progressoSoma = 0;
    let horasTotais = 0;
    const recursosPorTipo = {};
    let custoTotal = 0;

    atividades.forEach(a => {
      porStatus[a.status] = (porStatus[a.status] || 0) + 1;
      progressoSoma += Number(a.progresso) || 0;
      horasTotais += Number(a.duracaoHoras) || 0;
      (a.recursos || []).forEach(r => {
        recursosPorTipo[r.tipo] = (recursosPorTipo[r.tipo] || 0) + (Number(r.quantidade) || 0);
        custoTotal += (Number(r.quantidade) || 0) * (Number(r.custoUnitario) || 0);
      });
    });

    const progressoMedio = total > 0 ? roundTo(progressoSoma / total, 1) : 0;
    const { inicio, fim } = State.faixaDataParada(paradaId);
    const duracaoTotalParadaHoras = (inicio && fim) ? roundTo((fim - inicio) / 3600000, 1) : null;

    return { total, porStatus, progressoMedio, horasTotais, recursosPorTipo, custoTotal, inicio, fim, duracaoTotalParadaHoras };
  }

  function render() {
    const el = document.getElementById('view-resumo');
    const parada = State.getParadaAtiva();
    if (!parada) {
      el.innerHTML = `<div class="empty-state">Nenhuma parada selecionada. Cadastre ou escolha uma parada na aba "Paradas".</div>`;
      return;
    }
    const s = calcularEstatisticas(parada.id);

    el.innerHTML = `
      <div class="view-header">
        <h2>Resumo — ${escapeHtml(parada.nome)}</h2>
      </div>
      <div class="stat-cards">
        <div class="stat-card"><div class="stat-value">${s.total}</div><div class="stat-label">Atividades cadastradas</div></div>
        <div class="stat-card"><div class="stat-value">${s.progressoMedio}%</div><div class="stat-label">Progresso médio</div></div>
        <div class="stat-card"><div class="stat-value">${s.duracaoTotalParadaHoras !== null ? formatHoras(s.duracaoTotalParadaHoras) : '—'}</div><div class="stat-label">Duração total da parada</div></div>
        <div class="stat-card"><div class="stat-value">${formatHoras(s.horasTotais)}</div><div class="stat-label">Soma das durações das atividades</div></div>
        <div class="stat-card"><div class="stat-value">${s.custoTotal > 0 ? 'R$ ' + s.custoTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) : '—'}</div><div class="stat-label">Custo estimado de recursos</div></div>
      </div>

      <div class="resumo-cols">
        <div class="card">
          <h3>Atividades por status</h3>
          <div class="status-bar-chart mt-8">
            ${Object.keys(STATUS_LABELS).map(k => {
              const qtd = s.porStatus[k] || 0;
              const pct = s.total > 0 ? Math.round((qtd / s.total) * 100) : 0;
              return `
                <div class="status-bar-row">
                  <span>${STATUS_LABELS[k]}</span>
                  <div class="status-bar-track"><div class="status-bar-fill" style="width:${pct}%; background:${STATUS_COLORS[k]}"></div></div>
                  <span>${qtd}</span>
                </div>`;
            }).join('')}
          </div>
        </div>

        <div class="card">
          <h3>Recursos por tipo (quantidade)</h3>
          <div class="status-bar-chart mt-8">
            ${Object.keys(s.recursosPorTipo).length === 0 ? '<span class="text-muted">Nenhum recurso cadastrado.</span>' :
              Object.entries(s.recursosPorTipo).map(([tipo, qtd]) => `
                <div class="status-bar-row" style="grid-template-columns: 110px 1fr 60px;">
                  <span>${tipo.replace('_', ' ')}</span>
                  <div class="status-bar-track"><div class="status-bar-fill" style="width:100%; background:#2563eb"></div></div>
                  <span>${roundTo(qtd, 2)}</span>
                </div>`).join('')}
          </div>
        </div>
      </div>

      <div class="card mt-8">
        <h3>Janela da parada</h3>
        <p class="text-muted mt-8">Início mais cedo: <strong>${s.inicio ? formatDateTime(s.inicio) : '—'}</strong> · Fim mais tarde: <strong>${s.fim ? formatDateTime(s.fim) : '—'}</strong></p>
      </div>
    `;
  }

  return { render, calcularEstatisticas };
})();
