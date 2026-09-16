/* Inicialização, navegação entre abas e wiring dos controles globais */

(function () {
  let abaAtual = 'resumo';

  const RENDERERS = {
    resumo: () => UIResumo.render(),
    paradas: () => UIParadasCalendarios.render(),
    calendarios: () => UIParadasCalendarios.render(),
    atividades: () => UIAtividades.render(),
    tabela: () => UITabela.render(),
    gantt: () => UIGantt.render(),
    relatorios: () => {
      UIParadasCalendarios.render();
      const preview = document.getElementById('relatorio-preview');
      if (!preview.innerHTML.trim()) UIRelatorios.render();
    }
  };

  function renderAbaAtual() {
    UIParadasCalendarios.render(); // mantém seletor de parada e header sempre atualizados
    const fn = RENDERERS[abaAtual];
    if (fn) fn();
  }

  function irParaAba(nome) {
    abaAtual = nome;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.dataset.tab === nome));
    document.querySelectorAll('.view').forEach(v => v.classList.toggle('active', v.id === `view-${nome}`));
    renderAbaAtual();
  }

  function wireTopbar() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.addEventListener('click', () => irParaAba(btn.dataset.tab));
    });

    document.getElementById('seletor-parada').addEventListener('change', (e) => {
      if (e.target.value) State.setParadaAtiva(e.target.value);
    });

    document.getElementById('btn-nova-parada').addEventListener('click', () => UIParadasCalendarios.abrirFormParada(null));
    document.getElementById('btn-novo-calendario').addEventListener('click', () => UIParadasCalendarios.abrirFormCalendario(null));
    document.getElementById('btn-nova-atividade').addEventListener('click', () => UIAtividades.abrirFormAtividade(null));

    document.getElementById('gantt-zoom').addEventListener('change', () => UIGantt.render());

    document.getElementById('btn-pasta').addEventListener('click', () => Storage.conectarPastaSalva());
    document.getElementById('btn-trocar-pasta').addEventListener('click', () => {
      if (confirm('Selecionar uma pasta diferente para salvar os dados a partir de agora?')) Storage.escolherPasta();
    });

    document.getElementById('btn-exportar').addEventListener('click', () => {
      Storage.exportJson(State.getData());
      showToast('Backup exportado.');
    });

    const inputImportar = document.getElementById('input-importar');
    document.getElementById('btn-importar').addEventListener('click', () => inputImportar.click());
    inputImportar.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        if (!confirm('Importar este arquivo vai substituir todos os dados atuais do sistema. Deseja continuar?')) {
          e.target.value = '';
          return;
        }
        const dados = await Storage.importJsonFile(file);
        State.substituirTudo(dados);
        showToast('Dados importados com sucesso.');
      } catch (err) {
        console.error(err);
        showToast('Não foi possível importar o arquivo. Verifique se é um backup válido.', true);
      }
      e.target.value = '';
    });

    UIRelatorios.wireBotoes();
    Modal.wireGlobalClose();
  }

  async function iniciar() {
    wireTopbar();
    if (!Storage.suportaSistemaArquivos()) {
      document.getElementById('btn-pasta').title = 'Este navegador não suporta escolher uma pasta diretamente. Os dados ficam salvos no navegador; use Exportar/Importar para manter backups em arquivo.';
    }
    await State.init();
    State.onChange(() => {
      if (abaAtual === 'relatorios') {
        // não força re-render do relatório aberto para não perder o botão de imprimir sem necessidade
        UIParadasCalendarios.render();
      } else {
        renderAbaAtual();
      }
    });
    irParaAba('resumo');
  }

  document.addEventListener('DOMContentLoaded', iniciar);
})();
