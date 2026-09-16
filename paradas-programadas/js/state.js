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
      if (a.predecessoraId === undefined) a.predecessoraId = null;
      if (a.defasagemHoras === undefined) a.defasagemHoras = 0;
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
    recalcularProgramacao(parada.id);
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
    data.paradas.filter(p => p.calendarioId === cal.id).forEach(p => recalcularProgramacao(p.id));
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
    // Com predecessora definida, a Data Início é derivada automaticamente pela
    // cadeia (recalcularProgramacao, logo abaixo) — o que foi digitado aqui é ignorado.
    if (!atividade.predecessoraId) {
      const calendario = calendarioDaAtividade(atividade);
      const inicio = new Date(atividade.dataInicio);
      if (modoCalculo === 'fim' && atividade.dataFim) {
        atividade.duracaoHoras = calcularDuracaoHoras(inicio, new Date(atividade.dataFim), calendario);
      } else {
        const fim = calcularDataFim(inicio, Number(atividade.duracaoHoras) || 0, calendario);
        atividade.dataFim = fim ? fim.toISOString() : null;
      }
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
    recalcularProgramacao(atividade.paradaId);
    persist();
    return atividade;
  }

  function excluirAtividade(id) {
    const alvo = getAtividade(id);
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
    // atividades que dependiam de algo removido passam a ter data/hora manual (mantém o último valor calculado)
    data.atividades.forEach(a => {
      if (a.predecessoraId && idsParaExcluir.has(a.predecessoraId)) a.predecessoraId = null;
    });
    data.atividades = data.atividades.filter(a => !idsParaExcluir.has(a.id));
    if (alvo) recalcularProgramacao(alvo.paradaId);
    persist();
  }

  // ---------- Predecessoras / sucessoras ----------

  /** Atividades (da mesma parada) que têm `atividadeId` como predecessora direta. */
  function sucessorasDiretas(atividadeId) {
    return data.atividades.filter(a => a.predecessoraId === atividadeId);
  }

  /** IDs de `atividadeId` + todas as suas sucessoras diretas/indiretas (cadeia completa). */
  function cadeiaSucessoras(atividadeId, visitados = new Set()) {
    if (visitados.has(atividadeId)) return visitados;
    visitados.add(atividadeId);
    sucessorasDiretas(atividadeId).forEach(s => cadeiaSucessoras(s.id, visitados));
    return visitados;
  }

  /**
   * Recalcula Data Início/Fim de todas as atividades de uma parada, respeitando a
   * cadeia de predecessoras: quem tem predecessora tem sua Data Início derivada
   * automaticamente de "Data Fim da predecessora + defasagem"; quem não tem
   * predecessora mantém a Data Início que foi digitada manualmente. Percorre a
   * cadeia em profundidade (predecessora antes de sucessora) para propagar
   * mudanças em cascata, e se protege contra referência circular.
   */
  function recalcularProgramacao(paradaId) {
    const parada = getParada(paradaId);
    const calendario = parada ? getCalendario(parada.calendarioId) : calendarioPadrao();
    const todas = listarAtividadesDaParada(paradaId);
    const porId = new Map(todas.map(a => [a.id, a]));
    const processadas = new Set();

    function processar(a, pilha) {
      if (!a || processadas.has(a.id) || pilha.has(a.id)) return;
      pilha.add(a.id);
      if (a.predecessoraId && porId.has(a.predecessoraId)) {
        const pred = porId.get(a.predecessoraId);
        processar(pred, pilha);
        if (pred.dataFim) {
          const lag = Number(a.defasagemHoras) || 0;
          a.dataInicio = new Date(new Date(pred.dataFim).getTime() + lag * 3600000).toISOString();
        }
      }
      const fim = a.dataInicio ? calcularDataFim(new Date(a.dataInicio), Number(a.duracaoHoras) || 0, calendario) : null;
      a.dataFim = fim ? fim.toISOString() : null;
      processadas.add(a.id);
      pilha.delete(a.id);
    }

    todas.forEach(a => processar(a, new Set()));
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
    calendarioDaAtividade, faixaDataParada, duracaoRealHoras,
    sucessorasDiretas, cadeiaSucessoras, recalcularProgramacao
  };
})();
