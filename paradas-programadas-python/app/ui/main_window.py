"""Janela principal: menu, cabeçalho (parada ativa / pasta de trabalho),
navegação lateral e orquestração das páginas."""

from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import ttkbootstrap as tb

from .. import storage
from ..state import AppState
from .context import Contexto
from .theme import criar_janela_principal
from .tab_resumo import PaginaResumo
from .tab_paradas import PaginaParadas, PaginaCalendarios
from .tab_atividades import PaginaAtividades
from .tab_tabela import PaginaTabela
from .tab_gantt import PaginaGantt
from .tab_relatorios import PaginaRelatorios

NAV_ITENS = [
    ('resumo', '📊  Resumo'),
    ('paradas', '🛑  Paradas'),
    ('calendarios', '🗓  Calendários'),
    ('atividades', '📋  Atividades'),
    ('tabela', '📑  Tabela'),
    ('gantt', '📈  Gantt'),
    ('relatorios', '🖨  Relatórios'),
]


class JanelaPrincipal:
    def __init__(self):
        self.root = criar_janela_principal()
        self.state = AppState()
        self.ctx = Contexto(self.root, self.state)
        self._salvar_agendado = None
        self._nav_botoes = {}
        self._pagina_ativa = 'resumo'

        self.state.on_erro = lambda msg: self.ctx.toast(msg, erro=True)
        self.state.on_persist = self._agendar_salvar
        self.state.on_change(self._ao_mudar_estado)

        self._montar_menu()
        self._montar_corpo()
        self.root.protocol('WM_DELETE_WINDOW', self._sair)

        self._iniciar_workspace()

    # ---------------- estrutura da janela ----------------

    def _montar_menu(self):
        menu = tk.Menu(self.root)
        self.root.configure(menu=menu)

        arquivo = tk.Menu(menu, tearoff=False)
        arquivo.add_command(label='Abrir pasta de trabalho…', command=self._escolher_pasta)
        arquivo.add_separator()
        arquivo.add_command(label='Importar backup JSON…', command=self._importar_json)
        arquivo.add_command(label='Exportar backup JSON…', command=self._exportar_json)
        arquivo.add_separator()
        arquivo.add_command(label='Sair', command=self._sair)
        menu.add_cascade(label='Arquivo', menu=arquivo)

        ajuda = tk.Menu(menu, tearoff=False)
        ajuda.add_command(label='Sobre', command=self._sobre)
        menu.add_cascade(label='Ajuda', menu=ajuda)

    def _montar_corpo(self):
        cabecalho = tb.Frame(self.root, padding=(16, 10), bootstyle='dark')
        cabecalho.pack(fill='x', side='top')
        tb.Label(cabecalho, text='⏱ Paradas Programadas', font=('Segoe UI', 13, 'bold'),
                  bootstyle='inverse-dark').pack(side='left')

        direita = tb.Frame(cabecalho, bootstyle='dark')
        direita.pack(side='right')
        tb.Label(direita, text='Parada ativa:', bootstyle='inverse-dark').pack(side='left', padx=(0, 6))
        self.var_parada = tk.StringVar()
        self.combo_parada = tb.Combobox(direita, textvariable=self.var_parada, state='readonly', width=28)
        self.combo_parada.pack(side='left')
        self.combo_parada.bind('<<ComboboxSelected>>', self._ao_selecionar_parada)

        barra_status = tb.Frame(self.root, padding=(16, 4), bootstyle='secondary')
        barra_status.pack(fill='x', side='bottom')
        self.var_status = tk.StringVar(value='')
        self.ctx.registrar_status_var(self.var_status)
        tb.Label(barra_status, textvariable=self.var_status, bootstyle='inverse-secondary',
                  font=('Segoe UI', 9)).pack(side='left')

        corpo = tb.Frame(self.root)
        corpo.pack(fill='both', expand=True)

        sidebar = tb.Frame(corpo, bootstyle='dark', width=190)
        sidebar.pack(side='left', fill='y')
        sidebar.pack_propagate(False)
        for chave, rotulo in NAV_ITENS:
            btn = tb.Button(sidebar, text=rotulo, bootstyle='dark', command=lambda c=chave: self._ir_para(c))
            btn.pack(fill='x', padx=8, pady=(10 if chave == NAV_ITENS[0][0] else 2, 2))
            self._nav_botoes[chave] = btn

        self.area_conteudo = tb.Frame(corpo)
        self.area_conteudo.pack(side='left', fill='both', expand=True)
        self.area_conteudo.rowconfigure(0, weight=1)
        self.area_conteudo.columnconfigure(0, weight=1)

        self.paginas = {
            'resumo': PaginaResumo(self.area_conteudo, self.ctx),
            'paradas': PaginaParadas(self.area_conteudo, self.ctx),
            'calendarios': PaginaCalendarios(self.area_conteudo, self.ctx),
            'atividades': PaginaAtividades(self.area_conteudo, self.ctx),
            'tabela': PaginaTabela(self.area_conteudo, self.ctx),
            'gantt': PaginaGantt(self.area_conteudo, self.ctx),
            'relatorios': PaginaRelatorios(self.area_conteudo, self.ctx),
        }
        for pagina in self.paginas.values():
            pagina.grid(row=0, column=0, sticky='nsew')

        self._ir_para('resumo')

    def _ir_para(self, chave: str):
        self._pagina_ativa = chave
        for c, btn in self._nav_botoes.items():
            btn.configure(bootstyle='primary' if c == chave else 'dark')
        self.paginas[chave].tkraise()
        self.paginas[chave].atualizar()

    # ---------------- estado / parada ativa ----------------

    def _ao_mudar_estado(self):
        paradas = self.state.listar_paradas()
        nomes = [p['nome'] for p in paradas]
        self.combo_parada['values'] = nomes
        ativa = self.state.get_parada_ativa()
        if ativa:
            idx = next((i for i, p in enumerate(paradas) if p['id'] == ativa['id']), -1)
            if idx >= 0:
                self.combo_parada.current(idx)
        else:
            self.var_parada.set('')

        for pagina in self.paginas.values():
            pagina.atualizar()

    def _ao_selecionar_parada(self, _event=None):
        idx = self.combo_parada.current()
        paradas = self.state.listar_paradas()
        if 0 <= idx < len(paradas):
            self.state.set_parada_ativa(paradas[idx]['id'])

    # ---------------- pasta de trabalho ----------------

    def _iniciar_workspace(self):
        pasta = storage.obter_ultima_pasta() or storage.pasta_padrao()
        self._carregar_de(pasta)

    def _carregar_de(self, pasta: Path):
        dados = storage.carregar_workspace(pasta)
        self.state.carregar(dados)
        self.ctx.pasta_atual = pasta
        storage.definir_ultima_pasta(pasta)
        self.ctx.status_texto.set(self.ctx.status_base())
        if dados is None:
            storage.salvar_workspace(pasta, self.state.get_data())

    def _agendar_salvar(self, data: dict):
        if self._salvar_agendado:
            self.root.after_cancel(self._salvar_agendado)
        self._salvar_agendado = self.root.after(500, lambda: self._salvar_agora(data))

    def _salvar_agora(self, data: dict):
        if not self.ctx.pasta_atual:
            return
        try:
            storage.salvar_workspace(self.ctx.pasta_atual, data)
            self.ctx.status_texto.set(self.ctx.status_base())
        except OSError as e:
            self.ctx.toast(f'Erro ao salvar: {e}', erro=True)

    def _escolher_pasta(self):
        pasta = filedialog.askdirectory(parent=self.root, title='Escolher pasta de trabalho')
        if not pasta:
            return
        self._carregar_de(Path(pasta))
        self.ctx.toast(f'Pasta de trabalho: {pasta}')

    def _importar_json(self):
        caminho = filedialog.askopenfilename(
            parent=self.root, title='Importar backup JSON', filetypes=[('JSON', '*.json')])
        if not caminho:
            return
        if not messagebox.askyesno('Importar backup',
                                    'Importar este arquivo vai substituir todos os dados atuais. Deseja continuar?'):
            return
        try:
            dados = storage.importar_json(Path(caminho))
            self.state.substituir_tudo(dados)
            self.ctx.toast('Dados importados com sucesso.')
        except (OSError, ValueError) as e:
            messagebox.showerror('Erro ao importar', f'Não foi possível importar o arquivo:\n{e}', parent=self.root)

    def _exportar_json(self):
        destino = filedialog.asksaveasfilename(
            parent=self.root, title='Exportar backup JSON', defaultextension='.json',
            initialfile=storage.sugerir_nome_backup(), filetypes=[('JSON', '*.json')])
        if not destino:
            return
        try:
            storage.exportar_json(self.state.get_data(), Path(destino))
            self.ctx.toast('Backup exportado.')
        except OSError as e:
            messagebox.showerror('Erro ao exportar', str(e), parent=self.root)

    def _sobre(self):
        messagebox.showinfo(
            'Sobre',
            'Paradas Programadas\nSistema local de planejamento de paradas de manutenção.\n\n'
            'Roda inteiramente no seu computador — os dados ficam salvos na pasta de trabalho escolhida.',
            parent=self.root)

    def _sair(self):
        self.root.destroy()

    def run(self):
        self.root.mainloop()
