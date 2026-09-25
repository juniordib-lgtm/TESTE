/* UI: pré-visualização de imagens (galeria/lightbox) — reaproveitado pela lista de
   atividades, pelo formulário (que já está dentro de outro modal) e pelos relatórios.
   Usa sua própria camada de overlay (não o Modal genérico) para poder ficar
   empilhada por cima de um formulário aberto sem destruí-lo. */

const UIImagens = (() => {

  function fechar() {
    const el = document.getElementById('lightbox-overlay');
    if (el) el.remove();
    document.removeEventListener('keydown', onKeydown);
  }

  function onKeydown(e) {
    if (e.key === 'Escape') fechar();
  }

  function abrirGaleria(titulo, imagens, indiceInicial = 0) {
    if (!imagens || imagens.length === 0) {
      showToast('Nenhuma imagem para exibir.', true);
      return;
    }
    fechar(); // garante que não haja outra instância aberta
    let indice = Math.max(0, Math.min(indiceInicial, imagens.length - 1));

    const overlay = document.createElement('div');
    overlay.id = 'lightbox-overlay';
    overlay.className = 'modal-overlay lightbox-overlay';
    overlay.innerHTML = `
      <div class="modal">
        <h3>🖼 ${escapeHtml(titulo)}</h3>
        <div class="lightbox">
          <button type="button" class="lightbox-nav" id="lb-prev" ${imagens.length < 2 ? 'hidden' : ''}>‹</button>
          <div class="lightbox-main">
            <img id="lb-img" src="" alt="">
            <div class="lightbox-caption" id="lb-caption"></div>
          </div>
          <button type="button" class="lightbox-nav" id="lb-next" ${imagens.length < 2 ? 'hidden' : ''}>›</button>
        </div>
        <div class="lightbox-thumbs" id="lb-thumbs"></div>
        <div class="modal-close-row">
          <button type="button" class="btn btn-secondary" id="btn-fechar-galeria">Fechar</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);

    const img = overlay.querySelector('#lb-img');
    const caption = overlay.querySelector('#lb-caption');
    const thumbs = overlay.querySelector('#lb-thumbs');

    function render() {
      img.src = imagens[indice].dataUrl;
      img.alt = imagens[indice].nome || '';
      caption.textContent = `${imagens[indice].nome || 'imagem'} (${indice + 1}/${imagens.length})`;
      thumbs.querySelectorAll('.lightbox-thumb').forEach((t, i) => t.classList.toggle('active', i === indice));
    }

    thumbs.innerHTML = imagens.map((im, i) => `
      <div class="lightbox-thumb" data-i="${i}"><img src="${im.dataUrl}" alt=""></div>
    `).join('');
    thumbs.querySelectorAll('.lightbox-thumb').forEach(t => {
      t.addEventListener('click', () => { indice = Number(t.dataset.i); render(); });
    });

    const prev = overlay.querySelector('#lb-prev');
    const next = overlay.querySelector('#lb-next');
    if (prev) prev.addEventListener('click', () => { indice = (indice - 1 + imagens.length) % imagens.length; render(); });
    if (next) next.addEventListener('click', () => { indice = (indice + 1) % imagens.length; render(); });

    overlay.querySelector('#btn-fechar-galeria').addEventListener('click', fechar);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) fechar(); });
    document.addEventListener('keydown', onKeydown);

    render();
  }

  return { abrirGaleria };
})();
