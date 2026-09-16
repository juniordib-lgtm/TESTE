/*
 * Camada de persistencia.
 *
 * - IndexedDB é o armazenamento principal: sempre funciona (inclusive
 *   abrindo o index.html direto com duplo clique), sem precisar de servidor.
 * - Quando o navegador suporta a File System Access API (Chrome/Edge) o
 *   usuário pode escolher uma pasta real no disco; a cada alteração o app
 *   também grava um arquivo "dados-paradas.json" (+ pasta "imagens" fica
 *   dentro do próprio json, em base64, para manter tudo em um único
 *   arquivo portátil) nessa pasta.
 * - Exportar/Importar JSON funciona sempre, como alternativa manual.
 */

const Storage = (() => {
  const DB_NAME = 'paradas-programadas-db';
  const DB_VERSION = 1;
  const STORE_DATA = 'workspace';
  const STORE_HANDLES = 'handles';
  const DATA_KEY = 'main';
  const HANDLE_KEY = 'pastaTrabalho';
  const FILE_NAME = 'dados-paradas.json';

  let db = null;
  let folderHandle = null;       // pasta ativa nesta sessão (permissão concedida)
  let pastaArmazenadaHandle = null; // pasta lembrada (pode precisar reconectar após reabrir o navegador)

  function openDb() {
    return new Promise((resolve, reject) => {
      const req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = () => {
        const _db = req.result;
        if (!_db.objectStoreNames.contains(STORE_DATA)) _db.createObjectStore(STORE_DATA);
        if (!_db.objectStoreNames.contains(STORE_HANDLES)) _db.createObjectStore(STORE_HANDLES);
      };
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  function idbGet(store, key) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(store, 'readonly');
      const req = tx.objectStore(store).get(key);
      req.onsuccess = () => resolve(req.result);
      req.onerror = () => reject(req.error);
    });
  }

  function idbSet(store, key, value) {
    return new Promise((resolve, reject) => {
      const tx = db.transaction(store, 'readwrite');
      tx.objectStore(store).put(value, key);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async function init() {
    try {
      db = await openDb();
    } catch (e) {
      console.error('Falha ao abrir IndexedDB', e);
      db = null;
    }
  }

  async function load() {
    if (!db) return null;
    try {
      const data = await idbGet(STORE_DATA, DATA_KEY);
      return data || null;
    } catch (e) {
      console.error('Falha ao carregar dados do IndexedDB', e);
      return null;
    }
  }

  const setStatusEl = () => document.getElementById('status-salvamento');

  function marcarSalvando() {
    const el = setStatusEl();
    if (el) { el.textContent = 'salvando…'; el.classList.add('saving'); el.classList.remove('error'); }
  }
  function marcarSalvo() {
    const el = setStatusEl();
    if (el) { el.textContent = 'tudo salvo · ' + new Date().toLocaleTimeString('pt-BR'); el.classList.remove('saving', 'error'); }
  }
  function marcarErro(msg) {
    const el = setStatusEl();
    if (el) { el.textContent = msg || 'erro ao salvar'; el.classList.add('error'); el.classList.remove('saving'); }
  }

  async function persistToIndexedDb(data) {
    if (!db) return;
    await idbSet(STORE_DATA, DATA_KEY, data);
  }

  async function persistToFolder(data) {
    if (!folderHandle) return;
    try {
      const perm = await folderHandle.queryPermission({ mode: 'readwrite' });
      if (perm !== 'granted') return; // precisa de novo gesto do usuário para reconceder
      const fileHandle = await folderHandle.getFileHandle(FILE_NAME, { create: true });
      const writable = await fileHandle.createWritable();
      await writable.write(JSON.stringify(data, null, 2));
      await writable.close();
    } catch (e) {
      console.error('Falha ao gravar na pasta escolhida', e);
      marcarErro('erro ao gravar na pasta');
    }
  }

  const saveDebounced = debounce(async (data) => {
    marcarSalvando();
    try {
      await persistToIndexedDb(data);
      await persistToFolder(data);
      marcarSalvo();
    } catch (e) {
      console.error(e);
      marcarErro();
    }
  }, 500);

  function save(data) {
    saveDebounced(data);
  }

  function suportaSistemaArquivos() {
    return typeof window.showDirectoryPicker === 'function';
  }

  function atualizarLabelPasta() {
    const el = document.getElementById('pasta-nome');
    if (el) {
      if (folderHandle) el.textContent = folderHandle.name;
      else if (pastaArmazenadaHandle) el.textContent = `${pastaArmazenadaHandle.name} (clique para reconectar)`;
      else el.textContent = 'não definida';
    }
    const btnTrocar = document.getElementById('btn-trocar-pasta');
    if (btnTrocar) btnTrocar.hidden = !pastaArmazenadaHandle;
  }

  /** No carregamento, tenta restaurar silenciosamente a pasta lembrada (sem abrir diálogo nenhum). */
  async function restaurarPastaSalva() {
    if (!db || !suportaSistemaArquivos()) return;
    try {
      const handle = await idbGet(STORE_HANDLES, HANDLE_KEY);
      if (!handle) return;
      pastaArmazenadaHandle = handle;
      const perm = await handle.queryPermission({ mode: 'readwrite' });
      if (perm === 'granted') {
        folderHandle = handle;
      }
      // Se a permissão não foi concedida automaticamente, a pasta continua
      // lembrada (pastaArmazenadaHandle) — basta 1 clique no botão "Pasta"
      // para reconectar, sem precisar escolher a pasta de novo.
      atualizarLabelPasta();
    } catch (e) {
      console.warn('Não foi possível restaurar a pasta salva anteriormente', e);
    }
  }

  /** Clique no botão principal "Pasta": conecta a pasta já lembrada, sem abrir um novo diálogo de seleção. */
  async function conectarPastaSalva() {
    if (folderHandle) {
      showToast(`Pasta já conectada: "${folderHandle.name}". Use "Trocar pasta" para escolher outra.`);
      return folderHandle;
    }
    if (!pastaArmazenadaHandle) {
      return escolherPasta();
    }
    try {
      const perm = await pastaArmazenadaHandle.requestPermission({ mode: 'readwrite' });
      if (perm === 'granted') {
        folderHandle = pastaArmazenadaHandle;
        atualizarLabelPasta();
        showToast(`Pasta "${folderHandle.name}" reconectada.`);
        return folderHandle;
      }
      showToast('Permissão de acesso à pasta não concedida.', true);
      return null;
    } catch (e) {
      console.error(e);
      showToast('Não foi possível reconectar à pasta salva.', true);
      return null;
    }
  }

  /** Escolha explícita de uma pasta nova (primeira vez, ou "Trocar pasta"). Sempre abre o diálogo do sistema. */
  async function escolherPasta() {
    if (!suportaSistemaArquivos()) {
      showToast('Seu navegador não suporta escolher uma pasta diretamente. Use Exportar/Importar para manter um backup em arquivo.', true);
      return null;
    }
    try {
      const handle = await window.showDirectoryPicker({ mode: 'readwrite' });
      folderHandle = handle;
      pastaArmazenadaHandle = handle;
      if (db) await idbSet(STORE_HANDLES, HANDLE_KEY, handle);
      atualizarLabelPasta();
      showToast(`Pasta "${handle.name}" selecionada. Os dados serão salvos automaticamente nela a partir de agora.`);
      return handle;
    } catch (e) {
      if (e.name !== 'AbortError') {
        console.error(e);
        showToast('Não foi possível acessar a pasta escolhida.', true);
      }
      return null;
    }
  }

  function exportJson(data) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    const ts = new Date().toISOString().slice(0, 16).replace(/[:T]/g, '-');
    a.href = url;
    a.download = `paradas-programadas-backup-${ts}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function importJsonFile(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = JSON.parse(reader.result);
          resolve(data);
        } catch (e) {
          reject(e);
        }
      };
      reader.onerror = reject;
      reader.readAsText(file);
    });
  }

  return {
    init,
    load,
    save,
    escolherPasta,
    conectarPastaSalva,
    restaurarPastaSalva,
    suportaSistemaArquivos,
    exportJson,
    importJsonFile,
    get pastaAtual() { return folderHandle; }
  };
})();
