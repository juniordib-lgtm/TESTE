"""
Aparência da aplicação: usa o ttkbootstrap (tema "flatly") para dar uma
cara moderna de sistema de gestão de manutenção — cores semânticas por
status, cartões, navegação lateral — sem precisar reimplementar do zero
todo o theming que o ttk puro não oferece.

Esta é uma dependência real do projeto (ver requirements.txt); sem ela o
`main.py` mostra uma mensagem clara em vez de travar com um traceback.
"""

import ttkbootstrap as tb  # noqa: F401  (reexportado para os módulos de UI)
from ttkbootstrap.constants import *  # noqa: F401,F403

TEMA = 'flatly'

# Paleta usada fora dos componentes prontos do ttkbootstrap (Canvas do Gantt,
# textos auxiliares, etc.) — mantém consistência com o tema "flatly".
CORES = {
    'primary': '#2563eb',
    'primary_dark': '#1d4ed8',
    'bg_sidebar': '#1e293b',
    'bg_sidebar_ativo': '#2563eb',
    'bg_app': '#f4f6f9',
    'painel': '#ffffff',
    'borda': '#e2e8f0',
    'texto': '#1e293b',
    'texto_muted': '#64748b',
    'verde': '#16a34a',
    'amarelo': '#d97706',
    'vermelho': '#dc2626',
    'cinza': '#94a3b8',
}

STATUS_BOOTSTYLE = {
    'planejada': 'info',
    'em_andamento': 'warning',
    'concluida': 'success',
    'atrasada': 'danger',
}

STATUS_COR_HEX = {
    'planejada': '#4338ca',
    'em_andamento': '#b45309',
    'concluida': '#15803d',
    'atrasada': '#b91c1c',
}


def criar_janela_principal() -> tb.Window:
    janela = tb.Window(themename=TEMA)
    janela.title('Paradas Programadas')
    janela.geometry('1280x800')
    janela.minsize(1024, 640)
    return janela
