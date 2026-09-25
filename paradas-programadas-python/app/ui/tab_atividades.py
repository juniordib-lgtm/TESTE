"""Aba Atividades: árvore hierárquica (sem limite de profundidade) via
ttk.Treeview + diálogo completo de cadastro/edição — nome, número da OS,
responsável, datas planejadas/reais, predecessora/sucessoras, recursos e
imagens."""

from __future__ import annotations
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as tb

from .. import imagens_util
from ..calendar_engine import calcular_data_fim, calcular_duracao_horas
from ..formatting import formatar_data_hora, formatar_horas
from ..state import STATUS_LABELS, TIPOS_RECURSO, novo_id
from .theme import STATUS_BOOTSTYLE
from .dialogs import criar_area_rolavel, abrir_galeria, CampoDataHora


class PaginaAtividades(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._montar_esqueleto()
        self.atualizar()

    def _montar_esqueleto(self):
        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 10))
        tb.Label(cabecalho, text='Atividades e Sub-atividades', font=('Segoe UI', 16, 'bold')).pack(side='left')
        tb.Button(cabecalho, text='+ Nova Atividade', bootstyle='primary',
                  command=lambda: abrir_form_atividade(self.ctx, None)).pack(side='right')

        barra = tb.Frame(self)
        barra.pack(fill='x', pady=(0, 8))
        self.btn_nova_sub = tb.Button(barra, text='+ Sub-atividade', bootstyle='outline-primary',
                                       command=self._nova_sub, state='disabled')
        self.btn_nova_sub.pack(side='left', padx=(0, 6))
        self.btn_editar = tb.Button(barra, text='Editar', bootstyle='outline-secondary',
                                     command=self._editar, state='disabled')
        self.btn_editar.pack(side='left', padx=(0, 6))
        self.btn_imagens = tb.Button(barra, text='🖼 Ver imagens', bootstyle='outline-secondary',
                                      command=self._ver_imagens, state='disabled')
        self.btn_imagens.pack(side='left', padx=(0, 6))
        self.btn_excluir = tb.Button(barra, text='Excluir', bootstyle='outline-danger',
                                      command=self._excluir, state='disabled')
        self.btn_excluir.pack(side='left')

        colunas = ('os', 'responsavel', 'status', 'inicio', 'fim', 'duracao', 'progresso', 'recursos', 'imagens')
        titulos = {'os': 'OS', 'responsavel': 'Responsável', 'status': 'Status', 'inicio': 'Início plan.',
                   'fim': 'Fim plan.', 'duracao': 'Duração', 'progresso': 'Progr.', 'recursos': 'Rec.', 'imagens': 'Img.'}
        larguras = {'os': 80, 'responsavel': 120, 'status': 110, 'inicio': 130, 'fim': 130,
                    'duracao': 80, 'progresso': 55, 'recursos': 45, 'imagens': 45}

        self.tree = tb.Treeview(self, columns=colunas, show='tree headings', bootstyle='primary')
        self.tree.heading('#0', text='Atividade')
        self.tree.column('#0', width=300, stretch=True)
        for c in colunas:
            self.tree.heading(c, text=titulos[c])
            self.tree.column(c, width=larguras[c], anchor='center' if c in ('progresso', 'recursos', 'imagens') else 'w')

        for status, cor in (('planejada', '#4338ca'), ('em_andamento', '#b45309'),
                             ('concluida', '#15803d'), ('atrasada', '#b91c1c')):
            self.tree.tag_configure(status, foreground=cor)

        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._atualizar_botoes())
        self.tree.bind('<Double-1>', lambda e: self._editar())

    # ---------------- população da árvore ----------------

    def atualizar(self):
        selecionado = self.tree.selection()
        selecionado_id = selecionado[0] if selecionado else None
        for item in self.tree.get_children():
            self.tree.delete(item)

        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            self.tree.insert('', 'end', text='Selecione ou cadastre uma parada primeiro (aba "Paradas").', values=())
            self._atualizar_botoes()
            return

        arvore = self.ctx.state.arvore_atividades(parada['id'])
        if not arvore:
            self.tree.insert('', 'end', text='Nenhuma atividade cadastrada. Clique em "+ Nova Atividade".', values=())
            self._atualizar_botoes()
            return

        def inserir(lista, pai_iid):
            for a in lista:
                valores = (
                    a.get('numeroOS') or '—',
                    a.get('responsavel') or '—',
                    STATUS_LABELS.get(a['status'], a['status']),
                    formatar_data_hora(a.get('dataInicio')),
                    formatar_data_hora(a.get('dataFim')),
                    formatar_horas(a.get('duracaoHoras')),
                    f"{a.get('progresso') or 0}%",
                    str(len(a.get('recursos') or [])),
                    str(len(a.get('imagens') or [])),
                )
                pred = self.ctx.state.get_atividade(a.get('predecessoraId')) if a.get('predecessoraId') else None
                prefixo = '🔗 ' if pred else ''
                self.tree.insert(pai_iid, 'end', iid=a['id'], text=prefixo + a['nome'],
                                  values=valores, tags=(a['status'],), open=True)
                inserir(a.get('subAtividades') or [], a['id'])

        inserir(arvore, '')
        if selecionado_id and self.tree.exists(selecionado_id):
            self.tree.selection_set(selecionado_id)
        self._atualizar_botoes()

    def _atividade_selecionada(self) -> dict | None:
        sel = self.tree.selection()
        if not sel:
            return None
        return self.ctx.state.get_atividade(sel[0])

    def _atualizar_botoes(self):
        a = self._atividade_selecionada()
        estado_base = 'normal' if a else 'disabled'
        self.btn_nova_sub.configure(state=estado_base)
        self.btn_editar.configure(state=estado_base)
        self.btn_excluir.configure(state=estado_base)
        tem_imagens = bool(a and a.get('imagens'))
        self.btn_imagens.configure(state='normal' if tem_imagens else 'disabled')

    def _nova_sub(self):
        a = self._atividade_selecionada()
        if a:
            abrir_form_atividade(self.ctx, None, parent_id_sugerido=a['id'])

    def _editar(self):
        a = self._atividade_selecionada()
        if a:
            abrir_form_atividade(self.ctx, a)

    def _ver_imagens(self):
        a = self._atividade_selecionada()
        if a and a.get('imagens'):
            abrir_galeria(self.ctx.root, a['nome'], a['imagens'])

    def _excluir(self):
        a = self._atividade_selecionada()
        if not a:
            return
        if messagebox.askyesno('Excluir atividade', f'Excluir "{a["nome"]}" (e sub-atividades, se houver)?'):
            self.ctx.state.excluir_atividade(a['id'])
            self.ctx.toast('Atividade excluída.')


# =====================================================================
# Diálogo de cadastro / edição
# =====================================================================

def abrir_form_atividade(ctx, atividade: dict | None, parent_id_sugerido: str | None = None):
    parada = ctx.state.get_parada_ativa()
    if not parada:
        ctx.toast('Selecione uma parada primeiro.', erro=True)
        return

    from ..dates import from_iso_utc
    from datetime import datetime as _dt

    editando = atividade is not None
    atividade = dict(atividade) if atividade else {
        'id': None, 'paradaId': parada['id'], 'parentId': parent_id_sugerido,
        'nome': '', 'numeroOS': '', 'descricao': '', 'responsavel': '', 'area': '',
        'status': 'planejada', 'progresso': 0,
        'dataInicio': None, 'duracaoHoras': 8, 'dataFim': None,
        'inicioReal': None, 'fimReal': None, 'predecessoraId': None, 'defasagemHoras': 0,
        'imagens': [], 'recursos': [],
    }
    calendario = ctx.state.calendario_da_atividade(atividade)

    inicio_dt = from_iso_utc(atividade.get('dataInicio')) or _dt.now().replace(minute=0, second=0, microsecond=0)
    fim_dt = from_iso_utc(atividade.get('dataFim'))
    if fim_dt is None:
        fim_dt = calcular_data_fim(inicio_dt, float(atividade.get('duracaoHoras') or 0), calendario)

    # não pode virar sub-atividade de si mesma nem de seu próprio descendente
    ids_indisponiveis_pai = ctx.state.cadeia_descendentes(atividade['id']) if atividade.get('id') else set()
    opcoes_pai = [a for a in ctx.state.lista_achatada(parada['id']) if a['id'] not in ids_indisponiveis_pai]

    # não pode escolher como predecessora a si mesma nem quem já depende dela
    ids_indisponiveis_pred = ctx.state.cadeia_sucessoras(atividade['id']) if atividade.get('id') else set()
    opcoes_predecessora = [a for a in ctx.state.listar_atividades_da_parada(parada['id']) if a['id'] not in ids_indisponiveis_pred]
    sucessoras = ctx.state.sucessoras_diretas(atividade['id']) if atividade.get('id') else []

    imagens_atual = list(atividade.get('imagens') or [])
    recursos_atual = [dict(r) for r in (atividade.get('recursos') or [])]

    janela = tb.Toplevel(ctx.root)
    janela.title('Editar Atividade' if editando else 'Nova Atividade')
    janela.geometry('760x840')
    container, corpo = criar_area_rolavel(janela)
    container.pack(fill='both', expand=True, padx=4, pady=4)

    def secao(titulo):
        lf = tb.Labelframe(corpo, text=titulo, padding=12)
        lf.pack(fill='x', padx=10, pady=6)
        return lf

    # ---- Dados gerais ----
    geral = secao('Dados gerais')
    grid = tb.Frame(geral)
    grid.pack(fill='x')
    grid.columnconfigure(0, weight=3)
    grid.columnconfigure(1, weight=1)

    tb.Label(grid, text='Nome da atividade *', bootstyle='secondary').grid(row=0, column=0, sticky='w')
    tb.Label(grid, text='Número da OS (opcional)', bootstyle='secondary').grid(row=0, column=1, sticky='w', padx=(10, 0))
    var_nome = tk.StringVar(value=atividade['nome'])
    tb.Entry(grid, textvariable=var_nome).grid(row=1, column=0, sticky='ew', pady=(0, 8))
    var_os = tk.StringVar(value=atividade.get('numeroOS') or '')
    tb.Entry(grid, textvariable=var_os).grid(row=1, column=1, sticky='ew', padx=(10, 0), pady=(0, 8))

    tb.Label(geral, text='Esta é sub-atividade de:', bootstyle='secondary').pack(anchor='w')
    nomes_pai = ['— Nenhuma (atividade principal) —'] + [
        ('　　' * o['nivel']) + ('↳ ' if o['nivel'] > 0 else '') + o['nome'] for o in opcoes_pai
    ]
    var_pai_idx = tk.IntVar(value=0)
    combo_pai = tb.Combobox(geral, state='readonly', values=nomes_pai)
    idx_pai = next((i + 1 for i, o in enumerate(opcoes_pai) if o['id'] == atividade.get('parentId')), 0)
    combo_pai.current(idx_pai)
    combo_pai.pack(fill='x', pady=(0, 8))

    linha2 = tb.Frame(geral)
    linha2.pack(fill='x', pady=(0, 8))
    for i in range(4):
        linha2.columnconfigure(i, weight=1)
    tb.Label(linha2, text='Responsável', bootstyle='secondary').grid(row=0, column=0, sticky='w', padx=(0, 6))
    tb.Label(linha2, text='Área', bootstyle='secondary').grid(row=0, column=1, sticky='w', padx=(0, 6))
    tb.Label(linha2, text='Status', bootstyle='secondary').grid(row=0, column=2, sticky='w', padx=(0, 6))
    tb.Label(linha2, text='Progresso (%)', bootstyle='secondary').grid(row=0, column=3, sticky='w')
    var_resp = tk.StringVar(value=atividade.get('responsavel') or '')
    var_area = tk.StringVar(value=atividade.get('area') or '')
    tb.Entry(linha2, textvariable=var_resp).grid(row=1, column=0, sticky='ew', padx=(0, 6))
    tb.Entry(linha2, textvariable=var_area).grid(row=1, column=1, sticky='ew', padx=(0, 6))
    combo_status = tb.Combobox(linha2, state='readonly', values=list(STATUS_LABELS.values()))
    combo_status.set(STATUS_LABELS.get(atividade.get('status'), STATUS_LABELS['planejada']))
    combo_status.grid(row=1, column=2, sticky='ew', padx=(0, 6))
    var_progresso = tk.IntVar(value=int(atividade.get('progresso') or 0))
    tb.Spinbox(linha2, from_=0, to=100, textvariable=var_progresso, width=6).grid(row=1, column=3, sticky='ew')

    # ---- Datas planejadas ----
    datas = secao('Datas planejadas')
    tb.Label(datas, text='Data/Hora Início *', bootstyle='secondary').pack(anchor='w')
    campo_inicio = CampoDataHora(datas)
    campo_inicio.pack(anchor='w', pady=(0, 8))
    campo_inicio.set_datetime(inicio_dt)

    tb.Label(datas, text='Duração (horas) *', bootstyle='secondary').pack(anchor='w')
    var_duracao = tk.DoubleVar(value=float(atividade.get('duracaoHoras') or 0))
    tb.Spinbox(datas, from_=0, to=100000, increment=0.5, textvariable=var_duracao, width=10).pack(anchor='w', pady=(0, 8))

    tb.Label(datas, text='Data/Hora Fim (calculada — editar recalcula a duração)', bootstyle='secondary').pack(anchor='w')
    campo_fim = CampoDataHora(datas)
    campo_fim.pack(anchor='w', pady=(0, 4))
    campo_fim.set_datetime(fim_dt)

    modo_calculo = {'valor': 'duracao'}

    def recalcular_fim():
        ini = campo_inicio.get_datetime()
        if ini is None:
            return
        fim = calcular_data_fim(ini, float(var_duracao.get() or 0), calendario)
        campo_fim.set_datetime(fim)

    def recalcular_duracao():
        ini = campo_inicio.get_datetime()
        fim = campo_fim.get_datetime()
        if ini is None or fim is None:
            return
        var_duracao.set(calcular_duracao_horas(ini, fim, calendario))

    def ao_mudar_inicio():
        if modo_calculo['valor'] == 'duracao':
            recalcular_fim()
        else:
            recalcular_duracao()

    def ao_mudar_duracao(*_):
        modo_calculo['valor'] = 'duracao'
        recalcular_fim()

    def ao_mudar_fim():
        modo_calculo['valor'] = 'fim'
        recalcular_duracao()

    campo_inicio._on_change = ao_mudar_inicio
    campo_fim._on_change = ao_mudar_fim
    var_duracao.trace_add('write', ao_mudar_duracao)

    # ---- Sequenciamento ----
    seq = secao('Sequenciamento')
    tb.Label(seq, text=('Ligue esta atividade a uma predecessora para que a Data/Hora Início seja calculada '
                          'sozinha (fim da predecessora + defasagem) e acompanhe qualquer mudança nela.'),
              bootstyle='secondary', wraplength=650, justify='left').pack(anchor='w', pady=(0, 6))

    tb.Label(seq, text='Atividade predecessora', bootstyle='secondary').pack(anchor='w')
    nomes_pred = ['— Nenhuma (Data/Hora Início manual) —'] + [
        f"{o['nome']} (fim: {formatar_data_hora(o.get('dataFim'))})" for o in opcoes_predecessora
    ]
    combo_pred = tb.Combobox(seq, state='readonly', values=nomes_pred)
    idx_pred = next((i + 1 for i, o in enumerate(opcoes_predecessora) if o['id'] == atividade.get('predecessoraId')), 0)
    combo_pred.current(idx_pred)
    combo_pred.pack(fill='x', pady=(0, 8))

    tb.Label(seq, text='Defasagem após a predecessora (horas)', bootstyle='secondary').pack(anchor='w')
    var_defasagem = tk.DoubleVar(value=float(atividade.get('defasagemHoras') or 0))
    tb.Spinbox(seq, from_=-1000, to=1000, increment=0.5, textvariable=var_defasagem, width=10).pack(anchor='w', pady=(0, 8))

    tb.Label(seq, text='Sucessoras (dependem desta atividade)', bootstyle='secondary').pack(anchor='w')
    tb.Label(seq, text=', '.join(s['nome'] for s in sucessoras) or 'nenhuma', bootstyle='secondary').pack(anchor='w')

    def aplicar_predecessora(*_):
        idx = combo_pred.current()
        if idx > 0:
            pred = opcoes_predecessora[idx - 1]
            pred_fim = from_iso_utc(pred.get('dataFim'))
            lag = var_defasagem.get() or 0
            if pred_fim:
                from datetime import timedelta
                campo_inicio.set_datetime(pred_fim + timedelta(hours=lag))
            campo_inicio.set_somente_leitura(True)
            modo_calculo['valor'] = 'duracao'
            recalcular_fim()
        else:
            campo_inicio.set_somente_leitura(False)

    combo_pred.bind('<<ComboboxSelected>>', aplicar_predecessora)
    var_defasagem.trace_add('write', aplicar_predecessora)
    if idx_pred > 0:
        campo_inicio.set_somente_leitura(True)

    # ---- Execução real ----
    real = secao('Execução real')
    tb.Label(real, text='Preencha conforme a atividade realmente acontece. Deixe em branco enquanto não iniciada.',
              bootstyle='secondary', wraplength=650, justify='left').pack(anchor='w', pady=(0, 6))
    linha_real = tb.Frame(real)
    linha_real.pack(fill='x')
    col_ini = tb.Frame(linha_real)
    col_ini.pack(side='left', padx=(0, 20))
    tb.Label(col_ini, text='Início real', bootstyle='secondary').pack(anchor='w')
    campo_inicio_real = CampoDataHora(col_ini)
    campo_inicio_real.pack(anchor='w')
    campo_inicio_real.set_datetime(from_iso_utc(atividade.get('inicioReal')))

    col_fim = tb.Frame(linha_real)
    col_fim.pack(side='left')
    tb.Label(col_fim, text='Fim real', bootstyle='secondary').pack(anchor='w')
    campo_fim_real = CampoDataHora(col_fim)
    campo_fim_real.pack(anchor='w')
    campo_fim_real.set_datetime(from_iso_utc(atividade.get('fimReal')))

    lbl_duracao_real = tb.Label(real, text='Duração real: —', bootstyle='secondary')
    lbl_duracao_real.pack(anchor='w', pady=(6, 0))

    def recalcular_duracao_real():
        ini = campo_inicio_real.get_datetime()
        fim = campo_fim_real.get_datetime()
        if ini and fim:
            lbl_duracao_real.configure(text=f'Duração real: {formatar_horas(calcular_duracao_horas(ini, fim, calendario))}')
        elif ini and not fim:
            lbl_duracao_real.configure(text='Duração real: em andamento')
        else:
            lbl_duracao_real.configure(text='Duração real: —')

    campo_inicio_real._on_change = recalcular_duracao_real
    campo_fim_real._on_change = recalcular_duracao_real
    recalcular_duracao_real()

    # ---- Recursos ----
    rec_secao = secao('Recursos')
    rec_lista_frame = tb.Frame(rec_secao)
    rec_lista_frame.pack(fill='x')
    rotulos_tipo = list(TIPOS_RECURSO.values())
    chaves_tipo = list(TIPOS_RECURSO.keys())

    def redesenhar_recursos():
        for w in rec_lista_frame.winfo_children():
            w.destroy()
        if not recursos_atual:
            tb.Label(rec_lista_frame, text='Nenhum recurso adicionado.', bootstyle='secondary').pack(anchor='w')
        for idx, r in enumerate(recursos_atual):
            linha = tb.Frame(rec_lista_frame)
            linha.pack(fill='x', pady=2)
            v_tipo = tk.StringVar(value=TIPOS_RECURSO.get(r.get('tipo'), rotulos_tipo[0]))
            combo = tb.Combobox(linha, textvariable=v_tipo, state='readonly', values=rotulos_tipo, width=13)
            combo.pack(side='left', padx=(0, 4))
            v_nome = tk.StringVar(value=r.get('nome') or '')
            tb.Entry(linha, textvariable=v_nome, width=20).pack(side='left', padx=(0, 4))
            v_qtd = tk.StringVar(value=str(r.get('quantidade') if r.get('quantidade') is not None else ''))
            tb.Entry(linha, textvariable=v_qtd, width=6).pack(side='left', padx=(0, 4))
            v_unid = tk.StringVar(value=r.get('unidade') or '')
            tb.Entry(linha, textvariable=v_unid, width=8).pack(side='left', padx=(0, 4))
            v_custo = tk.StringVar(value=str(r.get('custoUnitario') if r.get('custoUnitario') is not None else ''))
            tb.Entry(linha, textvariable=v_custo, width=8).pack(side='left', padx=(0, 4))

            def _sync(idx=idx, v_tipo=v_tipo, v_nome=v_nome, v_qtd=v_qtd, v_unid=v_unid, v_custo=v_custo, *_):
                chave = chaves_tipo[rotulos_tipo.index(v_tipo.get())] if v_tipo.get() in rotulos_tipo else 'mao_de_obra'
                recursos_atual[idx].update(tipo=chave, nome=v_nome.get(), quantidade=v_qtd.get(), unidade=v_unid.get(), custoUnitario=v_custo.get())

            for var in (v_tipo, v_nome, v_qtd, v_unid, v_custo):
                var.trace_add('write', _sync)
            tb.Button(linha, text='✕', bootstyle='outline-danger', width=2,
                      command=lambda idx=idx: (recursos_atual.pop(idx), redesenhar_recursos())).pack(side='left')

    tb.Button(rec_secao, text='+ Adicionar recurso', bootstyle='outline-secondary',
              command=lambda: (recursos_atual.append({'id': novo_id(), 'tipo': 'mao_de_obra', 'nome': '', 'quantidade': 1, 'unidade': '', 'custoUnitario': ''}), redesenhar_recursos())).pack(anchor='w', pady=(6, 0))
    redesenhar_recursos()

    # ---- Imagens ----
    img_secao = secao('Imagens')
    img_lista_frame = tb.Frame(img_secao)
    img_lista_frame.pack(fill='x')

    def redesenhar_imagens():
        for w in img_lista_frame.winfo_children():
            w.destroy()
        if not imagens_atual:
            tb.Label(img_lista_frame, text='Nenhuma imagem anexada.', bootstyle='secondary').pack(anchor='w')
        for idx, img in enumerate(imagens_atual):
            linha = tb.Frame(img_lista_frame)
            linha.pack(fill='x', pady=2)
            tb.Label(linha, text=f"🖼 {img.get('nome') or 'imagem'}").pack(side='left', padx=(0, 8))
            tb.Button(linha, text='Ver', bootstyle='outline-secondary', width=5,
                      command=lambda idx=idx: abrir_galeria(janela, atividade.get('nome') or 'Imagens', imagens_atual, idx)).pack(side='left', padx=(0, 4))
            tb.Button(linha, text='✕', bootstyle='outline-danger', width=2,
                      command=lambda idx=idx: (imagens_atual.pop(idx), redesenhar_imagens())).pack(side='left')

    def adicionar_imagens():
        caminhos = filedialog.askopenfilenames(
            parent=janela, title='Selecionar imagens',
            filetypes=[('Imagens', '*.png *.jpg *.jpeg *.gif *.bmp *.webp'), ('Todos os arquivos', '*.*')])
        for c in caminhos:
            try:
                img = imagens_util.codificar_arquivo(c)
                img['id'] = novo_id()
                imagens_atual.append(img)
            except OSError as e:
                messagebox.showwarning('Erro ao ler imagem', str(e), parent=janela)
        redesenhar_imagens()

    tb.Button(img_secao, text='+ Adicionar imagens…', bootstyle='outline-secondary', command=adicionar_imagens).pack(anchor='w', pady=(6, 0))
    redesenhar_imagens()

    # ---- Descrição ----
    desc_secao = secao('Descrição')
    txt_desc = tk.Text(desc_secao, height=5, wrap='word')
    txt_desc.insert('1.0', atividade.get('descricao') or '')
    txt_desc.pack(fill='x')

    # ---- Rodapé ----
    def salvar():
        nome = var_nome.get().strip()
        if not nome:
            messagebox.showwarning('Campo obrigatório', 'Informe o nome da atividade.', parent=janela)
            return
        ini = campo_inicio.get_datetime()
        if ini is None:
            messagebox.showwarning('Campo obrigatório', 'Informe a Data/Hora Início.', parent=janela)
            return

        idx_pai_sel = combo_pai.current()
        parent_id = opcoes_pai[idx_pai_sel - 1]['id'] if idx_pai_sel > 0 else None
        idx_pred_sel = combo_pred.current()
        predecessora_id = opcoes_predecessora[idx_pred_sel - 1]['id'] if idx_pred_sel > 0 else None
        status_chave = next((k for k, v in STATUS_LABELS.items() if v == combo_status.get()), 'planejada')

        from ..dates import to_iso_utc
        fim = campo_fim.get_datetime()
        inicio_real = campo_inicio_real.get_datetime()
        fim_real = campo_fim_real.get_datetime()

        try:
            duracao = float(var_duracao.get() or 0)
        except (tk.TclError, ValueError):
            duracao = 0.0

        payload = {
            'id': atividade.get('id'), 'paradaId': parada['id'], 'parentId': parent_id,
            'nome': nome, 'numeroOS': var_os.get().strip(),
            'responsavel': var_resp.get().strip(), 'area': var_area.get().strip(),
            'status': status_chave, 'progresso': max(0, min(100, var_progresso.get())),
            'dataInicio': to_iso_utc(ini), 'duracaoHoras': duracao,
            'dataFim': to_iso_utc(fim) if fim else None,
            'inicioReal': to_iso_utc(inicio_real) if inicio_real else None,
            'fimReal': to_iso_utc(fim_real) if fim_real else None,
            'predecessoraId': predecessora_id, 'defasagemHoras': var_defasagem.get() or 0,
            'descricao': txt_desc.get('1.0', 'end').strip(),
            'ordem': atividade.get('ordem'),
            'imagens': imagens_atual,
            'recursos': [{
                'id': r.get('id') or novo_id(), 'tipo': r.get('tipo') or 'mao_de_obra',
                'nome': r.get('nome') or '', 'unidade': r.get('unidade') or '',
                'quantidade': float(r.get('quantidade') or 0) if str(r.get('quantidade') or '').strip() else 0,
                'custoUnitario': float(r.get('custoUnitario') or 0) if str(r.get('custoUnitario') or '').strip() else 0,
            } for r in recursos_atual],
        }
        ctx.state.salvar_atividade(payload, modo_calculo['valor'])
        ctx.toast('Atividade salva.')
        janela.destroy()

    rodape = tb.Frame(janela, padding=(14, 6, 14, 12))
    rodape.pack(fill='x')
    tb.Button(rodape, text='Cancelar', bootstyle='secondary', command=janela.destroy).pack(side='right', padx=(6, 0))
    tb.Button(rodape, text='Salvar', bootstyle='primary', command=salvar).pack(side='right')
    janela.transient(ctx.root)
    janela.grab_set()
