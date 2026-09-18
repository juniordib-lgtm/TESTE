/* Funções utilitárias gerais */

function uid() {
  return 'id-' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 9);
}

function pad2(n) { return String(n).padStart(2, '0'); }

/** Converte Date -> string "YYYY-MM-DDTHH:mm" para uso em <input type="datetime-local"> */
function toInputDateTime(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d)) return '';
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

/** Converte string do input datetime-local -> Date */
function fromInputDateTime(str) {
  if (!str) return null;
  const d = new Date(str);
  return isNaN(d) ? null : d;
}

function toInputDate(date) {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d)) return '';
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

/** Chave "YYYY-MM-DD" usada para excecoes de calendario */
function dateKey(date) {
  const d = new Date(date);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}`;
}

function formatDateTime(date) {
  if (!date) return '—';
  const d = new Date(date);
  if (isNaN(d)) return '—';
  return `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}/${d.getFullYear()} ${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

function formatDate(date) {
  if (!date) return '—';
  const d = new Date(date);
  if (isNaN(d)) return '—';
  return `${pad2(d.getDate())}/${pad2(d.getMonth() + 1)}/${d.getFullYear()}`;
}

function formatHoras(horas) {
  if (horas === null || horas === undefined || isNaN(horas)) return '—';
  if (horas < 24) return `${roundTo(horas, 1)}h`;
  const dias = Math.floor(horas / 24);
  const resto = roundTo(horas - dias * 24, 1);
  return resto > 0 ? `${dias}d ${resto}h` : `${dias}d`;
}

function roundTo(n, casas) {
  const f = Math.pow(10, casas);
  return Math.round(n * f) / f;
}

function debounce(fn, wait) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), wait);
  };
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function showToast(msg, isError = false) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.classList.toggle('error', isError);
  el.hidden = false;
  clearTimeout(showToast._t);
  showToast._t = setTimeout(() => { el.hidden = true; }, 3200);
}

const STATUS_LABELS = {
  planejada: 'Planejada',
  em_andamento: 'Em andamento',
  concluida: 'Concluída',
  atrasada: 'Atrasada'
};

const STATUS_COLORS = {
  planejada: '#4338ca',
  em_andamento: '#b45309',
  concluida: '#15803d',
  atrasada: '#b91c1c'
};

/** Modal genérico reutilizado por todos os formulários de cadastro. */
const Modal = (() => {
  const overlay = () => document.getElementById('modal-overlay');
  const box = () => document.getElementById('modal-box');

  function open(html, onMount) {
    box().innerHTML = html;
    overlay().hidden = false;
    document.body.style.overflow = 'hidden';
    if (typeof onMount === 'function') onMount(box());
  }

  function close() {
    overlay().hidden = true;
    box().innerHTML = '';
    document.body.style.overflow = '';
  }

  function wireGlobalClose() {
    overlay().addEventListener('click', (e) => {
      if (e.target === overlay()) close();
    });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !overlay().hidden) close();
    });
  }

  return { open, close, wireGlobalClose };
})();
