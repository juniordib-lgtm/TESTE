/*
 * Estado da aplicação em memória + operações de CRUD.
 * Toda alteração passa por `persist()`, que salva no IndexedDB / pasta
 * escolhida e dispara `onChange` para a UI se atualizar.
 */

const State = (() => {
  let data = criarWorkspaceVazio();
  let listeners = [];

  function criarWorkspaceVazio() {
    const cal = calendarioPadrao();
    return {
      version: 1,
      paradaAtivaId: null,
      paradas: [],
      calendarios: [cal],
      atividades: []
    };
  }

  function onChange(fn) { listeners.push(fn); }
  function notify() { listeners.forEach(fn => fn()); }

  function persist() {
    Storage.save(data);
    notify();
  }

  async function init() {
    await Storage.init();
    const loaded = await Storage.load();
    if (loaded && loaded.paradas) {
      data = migrar(loaded);
    }
    await Storage.restaurarPastaSalva();
    notify();
  }

  function migrar(d) {
    if (!d.calendarios || d.calendarios.length === 0) d.calendarios = [calendarioPadrao()];
    if (!d.atividades) d.atividades = [];
    if (!d.paradas) d.paradas = [];
    d.atividades.forEach(a => {
      if (!Array.isArray(a.imagens)) a.imagens = [];
      if (!Array.isArray(a.recursos)) a.recursos = [];
      if (a.progresso === undefined) a.progresso = 0;
      if (!a.status) a.status = 'planejada';
      if (a.inicioReal === undefined) a.inicioReal = null;
      if (a.fimReal === undefined) a.fimReal = null;
    });
    return d;
  }

  function substituirTudo(novoData) {
    data = migrar(novoData);
    persist();
  }

  function getData() { return data; }

  // ---------- Paradas ----------

  function listarParadas() { return data.paradas.slice().sort((a, b) => (a.criadoEm || '').localeCompare(b.criadoEm || '')); }

  function getParada(id) { return data.paradas.find(p => p.id === id) || null; }

  function getParadaAtiva() { return getParada(data.paradaAtivaId); }

  function setParadaAtiva(id) {
    data.paradaAtivaId = id;
    persist();
  }

  function salvarParada(parada) {
    if (!parada.calendarioId && data.calendarios[0]) parada.calendarioId = data.calendarios[0].id;
    const idx = data.paradas.findIndex(p => p.id === parada.id);
    if (idx >= 0) {
      data.paradas[idx] = parada;
    } else {
      parada.id = parada.id || uid();
      parada.criadoEm = new Date().toISOString();
      data.paradas.push(parada);
      if (!data.paradaAtivaId) data.paradaAtivaId = parada.id;
    }
    recalcularAtividadesDaParada(parada.id);
    persist();
    return parada;
  }

  function excluirParada(id) {
    data.paradas = data.paradas.filter(p => p.id !== id);
    data.atividades = data.atividades.filter(a => a.paradaId !== id);
    if (data.paradaAtivaId === id) {
      data.paradaAtivaId = data.paradas[0] ? data.paradas[0].id : null;
    }
    persist();
  }

  // ---------- Calendários ----------

  function listarCalendarios() { return data.calendarios; }
  function getCalendario(id) { return data.calendarios.find(c => c.id === id) || data.calendarios[0]; }

  function salvarCalendario(cal) {
    const idx = data.calendarios.findIndex(c => c.id === cal.id);
    if (idx >= 0) data.calendarios[idx] = cal;
    else { cal.id = cal.id || uid(); data.calendarios.push(cal); }
    // qualquer parada usando esse calendário precisa recalcular datas
    data.paradas.filter(p => p.calendarioId === cal.id).forEach(p => recalcularAtividadesDaParada(p.id));
    persist();
    return cal;
  }

  function excluirCalendario(id) {
    if (data.calendarios.length <= 1) {
      showToast('É preciso manter ao menos um calendário.', true);
      return false;
    }
    const emUso = data.paradas.some(p => p.calendarioId === id);
    if (emUso) {
      showToast('Este calendário está em uso por uma parada e não pode ser excluído.', true);
      return false;
    }
    data.calendarios = data.calendarios.filter(c => c.id !== id);
    persist();
    return true;
  }

  // ---------- Atividades ----------

  /** Ordenada por Data/Hora de Início (sem data vai para o final); empate usa a ordem de cadastro. */
  function listarAtividadesDaParada(paradaId) {
    return data.atividades.filter(a => a.paradaId === paradaId).sort((a, b) => {
      const da = a.dataInicio ? new Date(a.dataInicio).getTime() : Infinity;
      const db = b.dataInicio ? new Date(b.dataInicio).getTime() : Infinity;
      if (da !== db) return da - db;
      return (a.ordem || 0) - (b.ordem || 0);
    });
  }

  /** Retorna apenas as atividades de topo (sem parentId), cada uma com .subAtividades preenchido.
   *  Tanto as atividades de topo quanto as sub-atividades de cada uma ficam em ordem
   *  cronológica (Data/Hora de Início), e cada sub-atividade permanece agrupada
   *  logo abaixo da sua atividade correspondente. */
  function arvoreAtividades(paradaId) {
    const todas = listarAtividadesDaParada(paradaId);
    const porId = {};
    todas.forEach(a => { porId[a.id] = { ...a, subAtividades: [] }; });
    const raizes = [];
    todas.forEach(a => {
      if (a.parentId && porId[a.parentId]) {
        porId[a.parentId].subAtividades.push(porId[a.id]);
      } else {
        raizes.push(porId[a.id]);
      }
    });
    return raizes;
  }

  /** Achata a árvore em uma lista [{ ...atividade, nivel }], mantendo cada
   *  sub-atividade logo após a atividade correspondente (ordem de exibição
   *  usada pela listagem, pelo Gantt e pelos relatórios). */
  function listaAchatada(paradaId) {
    const out = [];
    (function visitar(lista, nivel) {
      lista.forEach(a => {
        const { subAtividades, ...resto } = a;
        out.push({ ...resto, nivel });
        visitar(subAtividades || [], nivel + 1);
      });
    })(arvoreAtividades(paradaId), 0);
    return out;
  }

  function getAtividade(id) { return data.atividades.find(a => a.id === id) || null; }

  function calendarioDaAtividade(atividade) {
    const parada = getParada(atividade.paradaId);
    return parada ? getCalendario(parada.calendarioId) : calendarioPadrao();
  }

  /** Duração real (horas produtivas), ou null se início e/ou fim real não estiverem preenchidos. */
  function duracaoRealHoras(atividade) {
    if (!atividade.inicioReal || !atividade.fimReal) return null;
    const calendario = calendarioDaAtividade(atividade);
    return calcularDuracaoHoras(new Date(atividade.inicioReal), new Date(atividade.fimReal), calendario);
  }

  /**
   * Salva uma atividade. `modoCalculo` indica qual campo foi editado por
   * último pelo usuário: 'duracao' (recalcula dataFim) ou 'fim' (recalcula
   * duracaoHoras). Default: 'duracao'.
   */
  function salvarAtividade(atividade, modoCalculo = 'duracao') {
    const calendario = calendarioDaAtividade(atividade);
    const inicio = new Date(atividade.dataInicio);

    if (modoCalculo === 'fim' && atividade.dataFim) {
      atividade.duracaoHoras = calcularDuracaoHoras(inicio, new Date(atividade.dataFim), calendario);
    } else {
      const fim = calcularDataFim(inicio, Number(atividade.duracaoHoras) || 0, calendario);
      atividade.dataFim = fim ? fim.toISOString() : null;
    }

    const idx = data.atividades.findIndex(a => a.id === atividade.id);
    if (idx >= 0) {
      data.atividades[idx] = atividade;
    } else {
      atividade.id = atividade.id || uid();
      atividade.ordem = atividade.ordem ?? (listarAtividadesDaParada(atividade.paradaId).length + 1);
      if (!Array.isArray(atividade.imagens)) atividade.imagens = [];
      if (!Array.isArray(atividade.recursos)) atividade.recursos = [];
      data.atividades.push(atividade);
    }
    persist();
    return atividade;
  }

  function excluirAtividade(id) {
    // exclui também as sub-atividades
    const idsParaExcluir = new Set([id]);
    let mudou = true;
    while (mudou) {
      mudou = false;
      data.atividades.forEach(a => {
        if (a.parentId && idsParaExcluir.has(a.parentId) && !idsParaExcluir.has(a.id)) {
          idsParaExcluir.add(a.id);
          mudou = true;
        }
      });
    }
    data.atividades = data.atividades.filter(a => !idsParaExcluir.has(a.id));
    persist();
  }

  function recalcularAtividadesDaParada(paradaId) {
    const calendario = (() => {
      const p = getParada(paradaId);
      return p ? getCalendario(p.calendarioId) : calendarioPadrao();
    })();
    listarAtividadesDaParada(paradaId).forEach(a => {
      const fim = calcularDataFim(new Date(a.dataInicio), Number(a.duracaoHoras) || 0, calendario);
      a.dataFim = fim ? fim.toISOString() : null;
    });
  }

  // ---------- Estatísticas ----------

  function faixaDataParada(paradaId) {
    const ativs = listarAtividadesDaParada(paradaId);
    if (ativs.length === 0) return { inicio: null, fim: null };
    let inicio = null, fim = null;
    ativs.forEach(a => {
      if (a.dataInicio) {
        const d = new Date(a.dataInicio);
        if (!inicio || d < inicio) inicio = d;
      }
      if (a.dataFim) {
        const d = new Date(a.dataFim);
        if (!fim || d > fim) fim = d;
      }
    });
    return { inicio, fim };
  }

  return {
    init, onChange, persist, getData, substituirTudo,
    listarParadas, getParada, getParadaAtiva, setParadaAtiva, salvarParada, excluirParada,
    listarCalendarios, getCalendario, salvarCalendario, excluirCalendario,
    listarAtividadesDaParada, arvoreAtividades, listaAchatada, getAtividade, salvarAtividade, excluirAtividade,
    calendarioDaAtividade, faixaDataParada, duracaoRealHoras
  };
})();
