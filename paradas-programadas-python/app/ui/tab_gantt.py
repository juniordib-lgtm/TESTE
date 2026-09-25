"""Aba Gantt: desenho customizado em Canvas, com zoom Semana/Dia/Horas —
barra sólida para o planejado e uma barra tracejada por baixo mostrando a
execução real, quando preenchida."""

from __future__ import annotations
import tkinter as tk
from datetime import datetime, timedelta
import ttkbootstrap as tb

from .. import dates
from ..formatting import formatar_data_hora, formatar_horas
from .theme import STATUS_COR_HEX

ALTURA_LINHA = 34
ALTURA_CABECALHO = 40
LARGURA_LABEL = 260


class PaginaGantt(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._linhas_layout = []  # [(atividade, nivel, y)]
        self._montar_esqueleto()
        self.atualizar()

    def _montar_esqueleto(self):
        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 10))
        tb.Label(cabecalho, text='Gantt', font=('Segoe UI', 16, 'bold')).pack(side='left')
        zoom_frame = tb.Frame(cabecalho)
        zoom_frame.pack(side='right')
        tb.Label(zoom_frame, text='Zoom:').pack(side='left', padx=(0, 6))
        self.var_zoom = tk.StringVar(value='Semana')
        combo = tb.Combobox(zoom_frame, textvariable=self.var_zoom, state='readonly',
                             values=['Semana', 'Dia', 'Horas'], width=10)
        combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>', lambda e: self.atualizar())

        legenda = tb.Frame(self)
        legenda.pack(fill='x', pady=(0, 6))
        self._legenda_item(legenda, '#2563eb', 'Planejado')
        self._legenda_item(legenda, '#64748b', 'Real (concluído)')
        self._legenda_item(legenda, '#f59e0b', 'Real (em andamento)')

        area = tb.Frame(self, bootstyle='light')
        area.pack(fill='both', expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(1, weight=1)

        self.canvas_labels = tk.Canvas(area, width=LARGURA_LABEL, highlightthickness=0, background='#ffffff')
        self.canvas_labels.grid(row=0, column=0, sticky='ns')

        self.canvas_timeline = tk.Canvas(area, highlightthickness=0, background='#ffffff')
        self.canvas_timeline.grid(row=0, column=1, sticky='nsew')

        self.scroll_y = tb.Scrollbar(area, orient='vertical', command=self._sync_yview)
        self.scroll_y.grid(row=0, column=2, sticky='ns')
        self.scroll_x = tb.Scrollbar(area, orient='horizontal', command=self.canvas_timeline.xview)
        self.scroll_x.grid(row=1, column=1, sticky='ew')

        self.canvas_labels.configure(yscrollcommand=self.scroll_y.set)
        self.canvas_timeline.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        for cv in (self.canvas_labels, self.canvas_timeline):
            cv.bind('<MouseWheel>', self._roda_mouse)
            cv.bind('<Shift-MouseWheel>', self._roda_mouse_horizontal)

    def _legenda_item(self, parent, cor, texto):
        item = tb.Frame(parent)
        item.pack(side='left', padx=(0, 16))
        marca = tk.Canvas(item, width=14, height=14, highlightthickness=0)
        marca.pack(side='left', padx=(0, 4))
        marca.create_rectangle(1, 1, 13, 13, fill=cor, outline=cor)
        tb.Label(item, text=texto, bootstyle='secondary', font=('Segoe UI', 9)).pack(side='left')

    def _sync_yview(self, *args):
        self.canvas_labels.yview(*args)
        self.canvas_timeline.yview(*args)

    def _roda_mouse(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas_labels.yview_scroll(delta, 'units')
        self.canvas_timeline.yview_scroll(delta, 'units')

    def _roda_mouse_horizontal(self, event):
        delta = -1 if event.delta > 0 else 1
        self.canvas_timeline.xview_scroll(delta, 'units')

    # ---------------- desenho ----------------

    def atualizar(self):
        self.canvas_labels.delete('all')
        self.canvas_timeline.delete('all')

        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            self.canvas_labels.create_text(10, 20, anchor='w', text='Selecione uma parada na aba "Paradas".')
            return

        linhas = [a for a in self.ctx.state.lista_achatada(parada['id']) if a.get('dataInicio') and a.get('dataFim')]
        if not linhas:
            self.canvas_labels.create_text(10, 20, anchor='w', text='Nenhuma atividade com datas definidas.')
            return

        range_inicio = min(dates.from_iso_utc(a['dataInicio']) for a in linhas)
        range_fim = max(dates.from_iso_utc(a['dataFim']) for a in linhas)
        for a in linhas:
            if a.get('inicioReal'):
                ini_r = dates.from_iso_utc(a['inicioReal'])
                fim_r = dates.from_iso_utc(a['fimReal']) if a.get('fimReal') else datetime.now()
                range_inicio = min(range_inicio, ini_r)
                range_fim = max(range_fim, fim_r)
        range_inicio -= timedelta(hours=12)
        range_fim += timedelta(hours=12)

        zoom = self.var_zoom.get()
        if zoom == 'Horas':
            unidades, col_w, granular_hora = self._horas_entre(range_inicio, range_fim), 30, True
        elif zoom == 'Dia':
            unidades, col_w, granular_hora = self._dias_entre(range_inicio, range_fim), 46, False
        else:
            unidades, col_w, granular_hora = self._dias_entre(range_inicio, range_fim), 20, False

        total_w = len(unidades) * col_w
        total_h = ALTURA_CABECALHO + len(linhas) * ALTURA_LINHA
        ms_total = (range_fim - range_inicio).total_seconds() * 1000
        px_por_ms = total_w / ms_total if ms_total else 1

        self.canvas_labels.configure(scrollregion=(0, 0, LARGURA_LABEL, total_h), height=min(total_h, 560))
        self.canvas_timeline.configure(scrollregion=(0, 0, total_w, total_h), height=min(total_h, 560))

        # cabeçalho
        self.canvas_labels.create_rectangle(0, 0, LARGURA_LABEL, ALTURA_CABECALHO, fill='#f8fafc', outline='#e2e8f0')
        self.canvas_labels.create_text(10, ALTURA_CABECALHO / 2, anchor='w', text='Atividade', font=('Segoe UI', 9, 'bold'))
        from ..calendar_engine import date_key
        hoje_key = date_key(datetime.now())

        x = 0
        for u in unidades:
            fim_dia = u.strftime('%Y-%m-%d') == hoje_key
            cor_fundo = '#fef9c3' if fim_dia else ('#f8fafc' if u.weekday() >= 5 else '#ffffff')
            self.canvas_timeline.create_rectangle(x, 0, x + col_w, total_h, fill=cor_fundo, outline='#f1f5f9')
            if granular_hora:
                rotulo = u.strftime('%Hh') if u.hour % 3 == 0 else ''
            else:
                rotulo = u.strftime('%d/%m')
            if rotulo:
                self.canvas_timeline.create_text(x + col_w / 2, ALTURA_CABECALHO / 2, text=rotulo, font=('Segoe UI', 8))
            x += col_w
        self.canvas_timeline.create_rectangle(0, 0, total_w, ALTURA_CABECALHO, fill='', outline='#e2e8f0')
        self.canvas_timeline.create_line(0, ALTURA_CABECALHO, total_w, ALTURA_CABECALHO, fill='#e2e8f0')

        def px(dt: datetime) -> float:
            return (dt - range_inicio).total_seconds() * 1000 * px_por_ms

        for i, a in enumerate(linhas):
            y = ALTURA_CABECALHO + i * ALTURA_LINHA
            nivel = a['nivel']
            cor_fundo_linha = '#ffffff' if i % 2 == 0 else '#f8fafc'
            self.canvas_labels.create_rectangle(0, y, LARGURA_LABEL, y + ALTURA_LINHA, fill=cor_fundo_linha, outline='#f1f5f9')
            prefixo = '↳ ' if nivel > 0 else ''
            if a.get('predecessoraId'):
                prefixo += '🔗 '
            texto_id = self.canvas_labels.create_text(12 + nivel * 14, y + ALTURA_LINHA / 2, anchor='w',
                                                        text=prefixo + a['nome'], font=('Segoe UI', 9), tags=(f"row-{a['id']}",))
            self.canvas_labels.tag_bind(texto_id, '<Button-1>', lambda e, aid=a['id']: self._abrir_edicao(aid))

            self.canvas_timeline.create_rectangle(0, y, total_w, y + ALTURA_LINHA, fill='', outline='#f1f5f9')

            ini = dates.from_iso_utc(a['dataInicio'])
            fim = dates.from_iso_utc(a['dataFim'])
            x1, x2 = px(ini), px(fim)
            cor = STATUS_COR_HEX.get(a['status'], '#2563eb')
            titulo = (f"{a['nome']}: {formatar_data_hora(a['dataInicio'])} → {formatar_data_hora(a['dataFim'])} "
                      f"({formatar_horas(a.get('duracaoHoras'))}, {a.get('progresso') or 0}%)")
            barra_id = self.canvas_timeline.create_rectangle(x1, y + 5, max(x1 + 6, x2), y + 22, fill=cor, outline=cor,
                                                               tags=(f"bar-{a['id']}",))
            self.canvas_timeline.tag_bind(barra_id, '<Button-1>', lambda e, aid=a['id']: self._abrir_edicao(aid))
            if x2 - x1 > 40:
                self.canvas_timeline.create_text((x1 + max(x1 + 6, x2)) / 2, y + 13, text=a['nome'][:30],
                                                   fill='white', font=('Segoe UI', 8))

            if a.get('inicioReal'):
                ini_r = dates.from_iso_utc(a['inicioReal'])
                fim_r = dates.from_iso_utc(a['fimReal']) if a.get('fimReal') else datetime.now()
                rx1, rx2 = px(ini_r), px(fim_r)
                cor_real = '#f59e0b' if not a.get('fimReal') else '#64748b'
                self.canvas_timeline.create_rectangle(rx1, y + 24, max(rx1 + 4, rx2), y + 30, fill=cor_real, outline=cor_real)

        self.canvas_timeline.create_rectangle(0, 0, total_w, total_h, outline='#e2e8f0')

    def _abrir_edicao(self, atividade_id):
        from .tab_atividades import abrir_form_atividade
        a = self.ctx.state.get_atividade(atividade_id)
        if a:
            abrir_form_atividade(self.ctx, a)

    @staticmethod
    def _dias_entre(inicio: datetime, fim: datetime) -> list[datetime]:
        dias = []
        cursor = datetime(inicio.year, inicio.month, inicio.day)
        limite = datetime(fim.year, fim.month, fim.day)
        while cursor <= limite:
            dias.append(cursor)
            cursor += timedelta(days=1)
        return dias

    @staticmethod
    def _horas_entre(inicio: datetime, fim: datetime) -> list[datetime]:
        horas = []
        cursor = inicio.replace(minute=0, second=0, microsecond=0)
        limite = fim.replace(minute=0, second=0, microsecond=0)
        while cursor <= limite:
            horas.append(cursor)
            cursor += timedelta(hours=1)
        return horas
