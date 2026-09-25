"""Widgets e diálogos reaproveitados por várias abas: painel rolável e a
galeria/lightbox de pré-visualização de imagens."""

from __future__ import annotations
import io
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import ttkbootstrap as tb

from .. import imagens_util
from .theme import CORES

try:
    from PIL import Image, ImageTk
    PIL_DISPONIVEL = True
except ImportError:
    PIL_DISPONIVEL = False


class CampoDataHora(tb.Frame):
    """Composto de data (com calendário via ttkbootstrap.DateEntry) + hora/minuto,
    substituindo o <input type="datetime-local"> nativo do navegador."""

    def __init__(self, parent, on_change=None, **kwargs):
        super().__init__(parent, **kwargs)
        self._on_change = on_change
        self._suprimir_evento = False

        self.data_entry = tb.DateEntry(self, date_format='%d/%m/%Y', value=None, width=11)
        self.data_entry.pack(side='left')
        tb.Label(self, text=' às ').pack(side='left')
        self.var_hora = tk.StringVar(value='08')
        self.var_min = tk.StringVar(value='00')
        sp_hora = tb.Spinbox(self, from_=0, to=23, width=3, format='%02.0f', textvariable=self.var_hora, wrap=True)
        sp_hora.pack(side='left')
        tb.Label(self, text=':').pack(side='left')
        sp_min = tb.Spinbox(self, from_=0, to=59, increment=5, width=3, format='%02.0f', textvariable=self.var_min, wrap=True)
        sp_min.pack(side='left')

        self.data_entry.entry.bind('<KeyRelease>', self._emitir)
        self.data_entry.entry.bind('<<DateEntrySelected>>', self._emitir)
        self.var_hora.trace_add('write', self._emitir)
        self.var_min.trace_add('write', self._emitir)
        self._entries = [self.data_entry.entry, self.data_entry.button, sp_hora, sp_min]

    def _emitir(self, *_):
        if not self._suprimir_evento and self._on_change:
            self._on_change()

    def get_datetime(self) -> datetime | None:
        data = self.data_entry.get_date()
        if data is None:
            return None
        try:
            hora = int(self.var_hora.get() or 0)
            minuto = int(self.var_min.get() or 0)
        except (ValueError, TypeError):
            hora = minuto = 0
        return datetime(data.year, data.month, data.day, hora, minuto)

    def set_datetime(self, dt: datetime | None):
        self._suprimir_evento = True
        try:
            self.data_entry.set_date(dt)
            self.var_hora.set(f'{dt.hour:02d}' if dt else '08')
            self.var_min.set(f'{dt.minute:02d}' if dt else '00')
        finally:
            self._suprimir_evento = False

    def set_somente_leitura(self, somente_leitura: bool):
        estado = 'disabled' if somente_leitura else 'normal'
        for w in self._entries:
            try:
                w.configure(state=estado)
            except tk.TclError:
                pass


def criar_area_rolavel(parent) -> tuple[tb.Frame, tb.Frame]:
    """Retorna (container, frame_interno). Adicione widgets em frame_interno."""
    container = tb.Frame(parent)
    canvas = tk.Canvas(container, highlightthickness=0, background=CORES['painel'])
    scrollbar = tb.Scrollbar(container, orient='vertical', command=canvas.yview)
    interno = tb.Frame(canvas)

    interno.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    janela_id = canvas.create_window((0, 0), window=interno, anchor='nw')
    canvas.bind('<Configure>', lambda e: canvas.itemconfig(janela_id, width=e.width))
    canvas.configure(yscrollcommand=scrollbar.set)

    def _on_roda(event):
        delta = -1 if event.delta > 0 else 1
        canvas.yview_scroll(delta, 'units')

    canvas.bind_all('<MouseWheel>', _on_roda, add='+')
    canvas.pack(side='left', fill='both', expand=True)
    scrollbar.pack(side='right', fill='y')
    return container, interno


class GaleriaImagens(tb.Toplevel):
    """Visualizador de imagens em tela cheia com navegação — equivalente ao
    lightbox da versão web. Funciona sem Pillow instalado (mostra um aviso
    e permite salvar/abrir a imagem no visualizador padrão do sistema)."""

    def __init__(self, parent, titulo: str, imagens: list[dict], indice_inicial: int = 0):
        super().__init__(parent)
        self.title(f'🖼 {titulo}')
        self.geometry('720x620')
        self.imagens = imagens
        self.indice = max(0, min(indice_inicial, len(imagens) - 1))
        self._foto_atual = None  # mantém referência viva (Tkinter descarta PhotoImage sem isso)

        topo = tb.Frame(self, padding=10)
        topo.pack(fill='both', expand=True)

        nav = tb.Frame(topo)
        nav.pack(fill='x')
        self.btn_prev = tb.Button(nav, text='◀', width=3, bootstyle='secondary', command=self._anterior)
        self.btn_prev.pack(side='left')
        self.lbl_legenda = tb.Label(nav, text='', anchor='center', font=('Segoe UI', 10))
        self.lbl_legenda.pack(side='left', fill='x', expand=True)
        self.btn_next = tb.Button(nav, text='▶', width=3, bootstyle='secondary', command=self._proxima)
        self.btn_next.pack(side='right')

        self.canvas_img = tk.Canvas(topo, background='#0f172a', highlightthickness=0)
        self.canvas_img.pack(fill='both', expand=True, pady=10)

        miniaturas = tb.Frame(topo)
        miniaturas.pack(fill='x')
        for i, img in enumerate(imagens):
            b = tb.Button(miniaturas, text=str(i + 1), width=3,
                          bootstyle='outline-secondary', command=lambda i=i: self._ir_para(i))
            b.pack(side='left', padx=2)

        rodape = tb.Frame(self, padding=(10, 0, 10, 10))
        rodape.pack(fill='x')
        tb.Button(rodape, text='Fechar', bootstyle='secondary', command=self.destroy).pack(side='right')
        if not PIL_DISPONIVEL:
            tb.Label(rodape, text='Instale "Pillow" (pip install Pillow) para pré-visualizar as fotos aqui.',
                     bootstyle='warning').pack(side='left')

        self.bind('<Left>', lambda e: self._anterior())
        self.bind('<Right>', lambda e: self._proxima())
        self.bind('<Escape>', lambda e: self.destroy())
        self.canvas_img.bind('<Configure>', lambda e: self._renderizar())
        self._renderizar()
        self.transient(parent)
        self.grab_set()

    def _anterior(self):
        self.indice = (self.indice - 1) % len(self.imagens)
        self._renderizar()

    def _proxima(self):
        self.indice = (self.indice + 1) % len(self.imagens)
        self._renderizar()

    def _ir_para(self, i: int):
        self.indice = i
        self._renderizar()

    def _renderizar(self):
        img = self.imagens[self.indice]
        self.lbl_legenda.configure(text=f"{img.get('nome') or 'imagem'} ({self.indice + 1}/{len(self.imagens)})")
        self.canvas_img.delete('all')
        if not PIL_DISPONIVEL:
            self.canvas_img.create_text(
                self.canvas_img.winfo_width() // 2 or 300, self.canvas_img.winfo_height() // 2 or 200,
                text='(pré-visualização indisponível sem Pillow)', fill='#94a3b8'
            )
            return
        try:
            dados = imagens_util.decodificar_data_url(img['dataUrl'])
            pil_img = Image.open(io.BytesIO(dados))
            pil_img.thumbnail((max(200, self.canvas_img.winfo_width() - 20),
                                max(200, self.canvas_img.winfo_height() - 20)))
            self._foto_atual = ImageTk.PhotoImage(pil_img)
            cx = max(1, self.canvas_img.winfo_width()) // 2
            cy = max(1, self.canvas_img.winfo_height()) // 2
            self.canvas_img.create_image(cx, cy, image=self._foto_atual)
        except Exception as e:  # noqa: BLE001 — imagem corrompida/formato não suportado, não deve travar a app
            self.canvas_img.create_text(300, 200, text=f'Não foi possível abrir esta imagem.\n({e})', fill='#f87171')


def abrir_galeria(parent, titulo: str, imagens: list[dict], indice_inicial: int = 0):
    if not imagens:
        messagebox.showinfo('Imagens', 'Nenhuma imagem para exibir.', parent=parent)
        return
    GaleriaImagens(parent, titulo, imagens, indice_inicial)


def miniatura_photoimage(data_url: str, tamanho=(64, 64)):
    """Retorna um ImageTk.PhotoImage pequeno para usar em listas, ou None
    se o Pillow não estiver disponível ou a imagem não puder ser lida."""
    if not PIL_DISPONIVEL:
        return None
    try:
        dados = imagens_util.decodificar_data_url(data_url)
        pil_img = Image.open(io.BytesIO(dados))
        pil_img.thumbnail(tamanho)
        return ImageTk.PhotoImage(pil_img)
    except Exception:  # noqa: BLE001
        return None
