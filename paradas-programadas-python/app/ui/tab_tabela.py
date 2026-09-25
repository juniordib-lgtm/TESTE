"""Aba Tabela: visão plana, ordenável por coluna e filtrável, com
exportação para Excel (.xlsx)."""

from __future__ import annotations
import tkinter as tk
from tkinter import filedialog, messagebox
import ttkbootstrap as tb

from .. import xlsx_writer
from ..formatting import formatar_data_hora, formatar_horas
from ..state import STATUS_LABELS, TIPOS_RECURSO
from .tab_atividades import abrir_form_atividade

COLUNAS = [
    ('nome', 'Atividade', 220),
    ('numeroOS', 'OS', 70),
    ('tipo', 'Tipo', 90),
    ('responsavel', 'Responsável', 110),
    ('area', 'Área', 90),
    ('status', 'Status', 100),
    ('predecessora', 'Predecessora', 130),
    ('dataInicio', 'Início planejado', 130),
    ('dataFim', 'Fim planejado', 130),
    ('duracaoHoras', 'Duração planej.', 100),
    ('inicioReal', 'Início real', 130),
    ('fimReal', 'Fim real', 130),
    ('progresso', 'Progresso', 70),
    ('qtdRecursos', 'Recursos', 60),
    ('qtdImagens', 'Imagens', 60),
]


class PaginaTabela(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._ordenacao = ('dataInicio', False)
        self._linhas_cache: list[dict] = []
        self._montar_esqueleto()
        self.atualizar()

    def _montar_esqueleto(self):
        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 10))
        tb.Label(cabecalho, text='Visão em Tabela', font=('Segoe UI', 16, 'bold')).pack(side='left')
        tb.Button(cabecalho, text='📊 Exportar Excel', bootstyle='success', command=self._exportar_excel).pack(side='right')

        filtros = tb.Frame(self)
        filtros.pack(fill='x', pady=(0, 8))
        tb.Label(filtros, text='Buscar:').pack(side='left', padx=(0, 4))
        self.var_busca = tk.StringVar()
        self.var_busca.trace_add('write', lambda *_: self.atualizar())
        tb.Entry(filtros, textvariable=self.var_busca, width=30).pack(side='left', padx=(0, 12))
        tb.Label(filtros, text='Status:').pack(side='left', padx=(0, 4))
        self.var_status = tk.StringVar(value='Todos')
        combo = tb.Combobox(filtros, textvariable=self.var_status, state='readonly',
                             values=['Todos'] + list(STATUS_LABELS.values()), width=16)
        combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>', lambda e: self.atualizar())

        chaves = [c[0] for c in COLUNAS]
        titulos = {c[0]: c[1] for c in COLUNAS}
        larguras = {c[0]: c[2] for c in COLUNAS}
        self.tree = tb.Treeview(self, columns=chaves, show='headings', bootstyle='primary')
        for c in chaves:
            self.tree.heading(c, text=titulos[c], command=lambda c=c: self._ordenar_por(c))
            self.tree.column(c, width=larguras[c], anchor='w')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', self._editar_selecionada)

    def _linhas(self) -> list[dict]:
        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            return []
        linhas = []
        for a in self.ctx.state.listar_atividades_da_parada(parada['id']):
            pred = self.ctx.state.get_atividade(a.get('predecessoraId')) if a.get('predecessoraId') else None
            linhas.append({
                **a,
                'tipoLabel': 'Sub-atividade' if a.get('parentId') else 'Atividade',
                'statusLabel': STATUS_LABELS.get(a['status'], a['status']),
                'predecessoraNome': pred['nome'] if pred else '',
                'qtdRecursos': len(a.get('recursos') or []),
                'qtdImagens': len(a.get('imagens') or []),
            })
        return linhas

    def _filtradas(self, linhas):
        busca = self.var_busca.get().strip().lower()
        status_sel = self.var_status.get()
        out = []
        for l in linhas:
            if status_sel != 'Todos' and l['statusLabel'] != status_sel:
                continue
            if busca:
                alvo = f"{l['nome']} {l.get('responsavel') or ''} {l.get('area') or ''} {l.get('numeroOS') or ''}".lower()
                if busca not in alvo:
                    continue
            out.append(l)
        return out

    def _ordenar_por(self, campo):
        atual_campo, atual_asc = self._ordenacao
        self._ordenacao = (campo, not atual_asc if campo == atual_campo else True)
        self.atualizar()

    def atualizar(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        linhas = self._filtradas(self._linhas())
        campo, asc = self._ordenacao

        def chave(l):
            v = {'dataInicio': l.get('dataInicio'), 'dataFim': l.get('dataFim'),
                 'inicioReal': l.get('inicioReal'), 'fimReal': l.get('fimReal')}.get(campo)
            if campo in ('dataInicio', 'dataFim', 'inicioReal', 'fimReal'):
                return v or ''
            val = l.get(campo, '')
            return val.lower() if isinstance(val, str) else val

        linhas.sort(key=chave, reverse=not asc)
        self._linhas_cache = linhas

        for l in linhas:
            prefixo = '↳ ' if l.get('parentId') else ''
            self.tree.insert('', 'end', iid=l['id'], values=(
                prefixo + l['nome'], l.get('numeroOS') or '—', l['tipoLabel'], l.get('responsavel') or '—',
                l.get('area') or '—', l['statusLabel'], l.get('predecessoraNome') or '—',
                formatar_data_hora(l.get('dataInicio')), formatar_data_hora(l.get('dataFim')),
                formatar_horas(l.get('duracaoHoras')),
                formatar_data_hora(l['inicioReal']) if l.get('inicioReal') else '—',
                formatar_data_hora(l['fimReal']) if l.get('fimReal') else '—',
                f"{l.get('progresso') or 0}%", l['qtdRecursos'], l['qtdImagens'],
            ))

    def _editar_selecionada(self, _event):
        sel = self.tree.selection()
        if sel:
            a = self.ctx.state.get_atividade(sel[0])
            if a:
                abrir_form_atividade(self.ctx, a)

    def _exportar_excel(self):
        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            self.ctx.toast('Selecione uma parada primeiro.', erro=True)
            return
        destino = filedialog.asksaveasfilename(
            parent=self, title='Exportar Excel', defaultextension='.xlsx',
            initialfile=f"{parada['nome']}.xlsx", filetypes=[('Planilha Excel', '*.xlsx')])
        if not destino:
            return

        linhas = self._linhas_cache or self._filtradas(self._linhas())
        colunas_ativ = ['Atividade', 'OS', 'Tipo', 'Responsável', 'Área', 'Status', 'Predecessora', 'Defasagem (h)',
                         'Início planejado', 'Fim planejado', 'Duração planejada (h)',
                         'Início real', 'Fim real', 'Duração real (h)',
                         'Progresso (%)', 'Recursos', 'Imagens', 'Descrição']
        linhas_ativ = []
        for l in linhas:
            dur_real = self.ctx.state.duracao_real_horas(l)
            linhas_ativ.append([
                ('↳ ' if l.get('parentId') else '') + l['nome'], l.get('numeroOS') or '', l['tipoLabel'],
                l.get('responsavel') or '', l.get('area') or '', l['statusLabel'],
                l.get('predecessoraNome') or '', l.get('defasagemHoras') if l.get('predecessoraNome') else '',
                formatar_data_hora(l.get('dataInicio')), formatar_data_hora(l.get('dataFim')), l.get('duracaoHoras') or 0,
                formatar_data_hora(l['inicioReal']) if l.get('inicioReal') else '',
                formatar_data_hora(l['fimReal']) if l.get('fimReal') else '',
                dur_real if dur_real is not None else '',
                l.get('progresso') or 0, l['qtdRecursos'], l['qtdImagens'], l.get('descricao') or '',
            ])

        colunas_rec = ['Atividade', 'Tipo de recurso', 'Recurso', 'Quantidade', 'Unidade', 'Custo unitário', 'Custo total']
        linhas_rec = []
        for l in linhas:
            for r in l.get('recursos') or []:
                qtd = float(r.get('quantidade') or 0)
                custo = float(r.get('custoUnitario') or 0)
                linhas_rec.append([l['nome'], TIPOS_RECURSO.get(r.get('tipo'), r.get('tipo') or ''),
                                    r.get('nome') or '', qtd, r.get('unidade') or '', custo, round(qtd * custo, 2)])

        try:
            xlsx_writer.salvar([
                {'nome': 'Atividades', 'colunas': colunas_ativ, 'linhas': linhas_ativ},
                {'nome': 'Recursos', 'colunas': colunas_rec, 'linhas': linhas_rec},
            ], destino)
            self.ctx.toast('Planilha Excel exportada.')
        except OSError as e:
            messagebox.showerror('Erro ao exportar', str(e), parent=self)
