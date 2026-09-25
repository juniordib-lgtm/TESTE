"""Abas Paradas e Calendários: cadastro (cards + diálogos)."""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as tb

from ..state import STATUS_LABELS, novo_id
from .theme import STATUS_BOOTSTYLE
from .dialogs import criar_area_rolavel

DIAS_SEMANA = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']


class PaginaParadas(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._montar_esqueleto()
        self.atualizar()

    def _montar_esqueleto(self):
        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 12))
        tb.Label(cabecalho, text='Paradas Programadas', font=('Segoe UI', 16, 'bold')).pack(side='left')
        tb.Button(cabecalho, text='+ Nova Parada', bootstyle='primary',
                  command=lambda: abrir_form_parada(self.ctx, None)).pack(side='right')
        self._container, self._lista = criar_area_rolavel(self)
        self._container.pack(fill='both', expand=True)

    def atualizar(self):
        for w in self._lista.winfo_children():
            w.destroy()

        paradas = self.ctx.state.listar_paradas()
        if not paradas:
            tb.Label(self._lista, text='Nenhuma parada cadastrada ainda. Clique em "+ Nova Parada" para começar.',
                      bootstyle='secondary').pack(pady=30)
            return

        ativa = self.ctx.state.get_parada_ativa()
        for i, p in enumerate(paradas):
            self._lista.columnconfigure(i % 2, weight=1)
            self._card_parada(self._lista, p, ativa and ativa['id'] == p['id']).grid(
                row=i // 2, column=i % 2, sticky='nsew', padx=6, pady=6)

    def _card_parada(self, parent, p, esta_ativa):
        cal = self.ctx.state.get_calendario(p.get('calendarioId'))
        qtd = len(self.ctx.state.listar_atividades_da_parada(p['id']))
        inicio, fim = self.ctx.state.faixa_data_parada(p['id'])
        from ..formatting import formatar_data
        estilo = 'primary' if esta_ativa else 'light'

        card = tb.Frame(parent, bootstyle=estilo, padding=14)
        titulo = tb.Frame(card)
        titulo.pack(fill='x')
        tb.Label(titulo, text=p['nome'], font=('Segoe UI', 12, 'bold'),
                  bootstyle=('inverse-primary' if esta_ativa else None)).pack(side='left')
        tb.Label(card, text=f"{p.get('local') or 'sem local definido'} · calendário: {cal['nome']}",
                  bootstyle=('inverse-primary' if esta_ativa else 'secondary'), font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 6))
        if p.get('descricao'):
            tb.Label(card, text=p['descricao'], wraplength=360,
                      bootstyle=('inverse-primary' if esta_ativa else 'secondary'), font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 6))
        periodo = f"{formatar_data(inicio) if inicio else '—'} a {formatar_data(fim) if fim else '—'}"
        tb.Label(card, text=f'{qtd} atividade(s) · {periodo}',
                  bootstyle=('inverse-primary' if esta_ativa else 'secondary'), font=('Segoe UI', 9)).pack(anchor='w')
        tb.Label(card, text=STATUS_LABELS.get(p.get('status'), p.get('status')),
                  bootstyle=STATUS_BOOTSTYLE.get(p.get('status'), 'secondary')).pack(anchor='w', pady=(6, 8))

        acoes = tb.Frame(card)
        acoes.pack(fill='x')
        if not esta_ativa:
            tb.Button(acoes, text='Definir como ativa', bootstyle='outline-primary',
                      command=lambda: self.ctx.state.set_parada_ativa(p['id'])).pack(side='left', padx=(0, 4))
        tb.Button(acoes, text='Editar', bootstyle='outline-secondary',
                  command=lambda: abrir_form_parada(self.ctx, p)).pack(side='left', padx=(0, 4))
        tb.Button(acoes, text='Excluir', bootstyle='outline-danger',
                  command=lambda: self._excluir(p)).pack(side='left')
        return card

    def _excluir(self, p):
        if messagebox.askyesno('Excluir parada',
                                f'Excluir "{p["nome"]}" e todas as suas atividades? Esta ação não pode ser desfeita.'):
            self.ctx.state.excluir_parada(p['id'])
            self.ctx.toast('Parada excluída.')


def abrir_form_parada(ctx, parada: dict | None):
    editando = parada is not None
    parada = dict(parada) if parada else {
        'id': None, 'nome': '', 'local': '', 'status': 'planejada',
        'calendarioId': None, 'descricao': '',
    }
    calendarios = ctx.state.listar_calendarios()

    janela = tb.Toplevel(ctx.root)
    janela.title('Editar Parada' if editando else 'Nova Parada')
    janela.geometry('520x480')
    corpo = tb.Frame(janela, padding=18)
    corpo.pack(fill='both', expand=True)

    tb.Label(corpo, text='Nome da parada *', bootstyle='secondary').pack(anchor='w')
    var_nome = tk.StringVar(value=parada['nome'])
    tb.Entry(corpo, textvariable=var_nome).pack(fill='x', pady=(0, 10))

    tb.Label(corpo, text='Local / Planta', bootstyle='secondary').pack(anchor='w')
    var_local = tk.StringVar(value=parada.get('local') or '')
    tb.Entry(corpo, textvariable=var_local).pack(fill='x', pady=(0, 10))

    linha = tb.Frame(corpo)
    linha.pack(fill='x', pady=(0, 10))
    esq = tb.Frame(linha)
    esq.pack(side='left', fill='x', expand=True, padx=(0, 6))
    tb.Label(esq, text='Status', bootstyle='secondary').pack(anchor='w')
    var_status = tk.StringVar(value=parada.get('status') or 'planejada')
    combo_status = tb.Combobox(esq, textvariable=var_status, state='readonly',
                                values=list(STATUS_LABELS.values()))
    combo_status.set(STATUS_LABELS.get(parada.get('status'), STATUS_LABELS['planejada']))
    combo_status.pack(fill='x')

    dir_ = tb.Frame(linha)
    dir_.pack(side='left', fill='x', expand=True, padx=(6, 0))
    tb.Label(dir_, text='Calendário utilizado *', bootstyle='secondary').pack(anchor='w')
    nomes_cal = [c['nome'] for c in calendarios]
    var_cal = tk.StringVar()
    combo_cal = tb.Combobox(dir_, textvariable=var_cal, state='readonly', values=nomes_cal)
    idx_cal = next((i for i, c in enumerate(calendarios) if c['id'] == parada.get('calendarioId')), 0)
    if nomes_cal:
        combo_cal.current(idx_cal)
    combo_cal.pack(fill='x')

    tb.Label(corpo, text='Descrição', bootstyle='secondary').pack(anchor='w')
    txt_desc = tk.Text(corpo, height=6, wrap='word')
    txt_desc.insert('1.0', parada.get('descricao') or '')
    txt_desc.pack(fill='both', expand=True, pady=(0, 10))

    def salvar():
        nome = var_nome.get().strip()
        if not nome:
            messagebox.showwarning('Campo obrigatório', 'Informe o nome da parada.', parent=janela)
            return
        if not calendarios:
            messagebox.showwarning('Sem calendário', 'Cadastre um calendário antes de criar uma parada.', parent=janela)
            return
        status_chave = next((k for k, v in STATUS_LABELS.items() if v == combo_status.get()), 'planejada')
        cal_id = calendarios[combo_cal.current()]['id'] if combo_cal.current() >= 0 else calendarios[0]['id']
        salvo = ctx.state.salvar_parada({
            'id': parada['id'], 'nome': nome, 'local': var_local.get().strip(),
            'status': status_chave, 'calendarioId': cal_id,
            'descricao': txt_desc.get('1.0', 'end').strip(),
        })
        if not editando:
            ctx.state.set_parada_ativa(salvo['id'])
        ctx.toast('Parada salva.')
        janela.destroy()

    rodape = tb.Frame(janela, padding=(18, 0, 18, 18))
    rodape.pack(fill='x')
    tb.Button(rodape, text='Cancelar', bootstyle='secondary', command=janela.destroy).pack(side='right', padx=(6, 0))
    tb.Button(rodape, text='Salvar', bootstyle='primary', command=salvar).pack(side='right')
    janela.transient(ctx.root)
    janela.grab_set()


# =====================================================================
# Calendários
# =====================================================================

class PaginaCalendarios(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._montar_esqueleto()
        self.atualizar()

    def _montar_esqueleto(self):
        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 4))
        tb.Label(cabecalho, text='Calendários', font=('Segoe UI', 16, 'bold')).pack(side='left')
        tb.Button(cabecalho, text='+ Novo Calendário', bootstyle='primary',
                  command=lambda: abrir_form_calendario(self.ctx, None)).pack(side='right')
        tb.Label(self, bootstyle='secondary', wraplength=900, justify='left', text=(
            'Um calendário define quantas horas por dia valem como "tempo produtivo" da parada, quais dias '
            'da semana são úteis e exceções (feriados, dias com capacidade reduzida). Ele é usado para calcular '
            'automaticamente a Data Fim das atividades a partir da duração informada.'
        )).pack(fill='x', pady=(0, 14))
        self._container, self._lista = criar_area_rolavel(self)
        self._container.pack(fill='both', expand=True)

    def atualizar(self):
        for w in self._lista.winfo_children():
            w.destroy()
        calendarios = self.ctx.state.listar_calendarios()
        for i, c in enumerate(calendarios):
            self._lista.columnconfigure(i % 2, weight=1)
            self._card_calendario(self._lista, c).grid(row=i // 2, column=i % 2, sticky='nsew', padx=6, pady=6)

    def _card_calendario(self, parent, c):
        dias_txt = ', '.join(DIAS_SEMANA[i] for i, v in enumerate(c.get('diasUteis') or []) if v) or 'nenhum'
        qtd_exc = len(c.get('excecoes') or {})
        card = tb.Frame(parent, bootstyle='light', padding=14)
        tb.Label(card, text=c['nome'], font=('Segoe UI', 12, 'bold')).pack(anchor='w')
        tb.Label(card, text=f"{c.get('horasPorDia')}h/dia produtivas · dias: {dias_txt}",
                  bootstyle='secondary', font=('Segoe UI', 9)).pack(anchor='w', pady=(2, 2))
        tb.Label(card, text=f'{qtd_exc} exceção(ões) cadastradas', bootstyle='secondary', font=('Segoe UI', 9)).pack(anchor='w', pady=(0, 8))
        acoes = tb.Frame(card)
        acoes.pack(fill='x')
        tb.Button(acoes, text='Editar', bootstyle='outline-secondary',
                  command=lambda: abrir_form_calendario(self.ctx, c)).pack(side='left', padx=(0, 4))
        tb.Button(acoes, text='Excluir', bootstyle='outline-danger',
                  command=lambda: self._excluir(c)).pack(side='left')
        return card

    def _excluir(self, c):
        if messagebox.askyesno('Excluir calendário', f'Excluir o calendário "{c["nome"]}"?'):
            if self.ctx.state.excluir_calendario(c['id']):
                self.ctx.toast('Calendário excluído.')


def abrir_form_calendario(ctx, calendario: dict | None):
    editando = calendario is not None
    calendario = dict(calendario) if calendario else {
        'id': None, 'nome': '', 'horasPorDia': 24,
        'diasUteis': [True] * 7, 'excecoes': {},
    }
    excecoes_atuais = list((calendario.get('excecoes') or {}).items())

    janela = tb.Toplevel(ctx.root)
    janela.title('Editar Calendário' if editando else 'Novo Calendário')
    janela.geometry('560x560')
    corpo = tb.Frame(janela, padding=18)
    corpo.pack(fill='both', expand=True)

    tb.Label(corpo, text='Nome *', bootstyle='secondary').pack(anchor='w')
    var_nome = tk.StringVar(value=calendario['nome'])
    tb.Entry(corpo, textvariable=var_nome).pack(fill='x', pady=(0, 10))

    tb.Label(corpo, text='Horas produtivas por dia (0-24) *', bootstyle='secondary').pack(anchor='w')
    var_horas = tk.DoubleVar(value=calendario.get('horasPorDia', 24))
    tb.Spinbox(corpo, from_=0, to=24, increment=0.5, textvariable=var_horas).pack(fill='x', pady=(0, 10))

    dias_frame = tb.Labelframe(corpo, text='Dias da semana úteis', padding=10)
    dias_frame.pack(fill='x', pady=(0, 10))
    vars_dias = []
    dias_uteis = calendario.get('diasUteis') or [True] * 7
    for i, nome in enumerate(DIAS_SEMANA):
        v = tk.BooleanVar(value=bool(dias_uteis[i]))
        vars_dias.append(v)
        tb.Checkbutton(dias_frame, text=nome, variable=v, bootstyle='round-toggle').pack(side='left', padx=4)

    exc_frame = tb.Labelframe(corpo, text='Exceções (feriados / capacidade diferente)', padding=10)
    exc_frame.pack(fill='both', expand=True, pady=(0, 10))
    linhas_exc_container = tb.Frame(exc_frame)
    linhas_exc_container.pack(fill='both', expand=True)
    linhas_widgets = []

    def redesenhar_excecoes():
        for w in linhas_exc_container.winfo_children():
            w.destroy()
        linhas_widgets.clear()
        for data_str, horas in excecoes_atuais:
            linha = tb.Frame(linhas_exc_container)
            linha.pack(fill='x', pady=2)
            v_data = tk.StringVar(value=data_str)
            v_horas = tk.StringVar(value=str(horas))
            tb.Entry(linha, textvariable=v_data, width=14).pack(side='left', padx=(0, 6))
            tb.Label(linha, text='data AAAA-MM-DD', bootstyle='secondary', font=('Segoe UI', 8)).pack(side='left', padx=(0, 10))
            tb.Entry(linha, textvariable=v_horas, width=6).pack(side='left', padx=(0, 6))
            tb.Label(linha, text='horas', bootstyle='secondary', font=('Segoe UI', 8)).pack(side='left')
            idx_atual = len(linhas_widgets)
            tb.Button(linha, text='✕', bootstyle='outline-danger', width=2,
                      command=lambda idx=idx_atual: remover(idx)).pack(side='right')
            linhas_widgets.append((v_data, v_horas))

    def remover(idx):
        del excecoes_atuais[idx]
        redesenhar_excecoes()

    def adicionar():
        excecoes_atuais.append(('', 0))
        redesenhar_excecoes()

    tb.Button(exc_frame, text='+ Adicionar exceção', bootstyle='outline-secondary', command=adicionar).pack(anchor='w', pady=(6, 0))
    redesenhar_excecoes()

    def salvar():
        nome = var_nome.get().strip()
        if not nome:
            messagebox.showwarning('Campo obrigatório', 'Informe o nome do calendário.', parent=janela)
            return
        excecoes = {}
        for v_data, v_horas in linhas_widgets:
            d = v_data.get().strip()
            if d:
                try:
                    excecoes[d] = float(v_horas.get() or 0)
                except ValueError:
                    messagebox.showwarning('Valor inválido', f'Horas inválidas para a exceção "{d}".', parent=janela)
                    return
        ctx.state.salvar_calendario({
            'id': calendario['id'], 'nome': nome,
            'horasPorDia': var_horas.get(),
            'diasUteis': [v.get() for v in vars_dias],
            'excecoes': excecoes,
        })
        ctx.toast('Calendário salvo.')
        janela.destroy()

    rodape = tb.Frame(janela, padding=(18, 0, 18, 18))
    rodape.pack(fill='x')
    tb.Button(rodape, text='Cancelar', bootstyle='secondary', command=janela.destroy).pack(side='right', padx=(6, 0))
    tb.Button(rodape, text='Salvar', bootstyle='primary', command=salvar).pack(side='right')
    janela.transient(ctx.root)
    janela.grab_set()
