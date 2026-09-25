"""Aba Resumo: painel com cartões de estatística, progresso por status e
recursos — equivalente ao dashboard da versão web."""

from __future__ import annotations
import ttkbootstrap as tb

from ..formatting import formatar_data_hora, formatar_horas, formatar_moeda
from ..state import STATUS_LABELS
from .theme import STATUS_BOOTSTYLE


class PaginaResumo(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._corpo = None
        self.atualizar()

    def atualizar(self):
        for w in self.winfo_children():
            w.destroy()

        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            tb.Label(self, text='Nenhuma parada selecionada. Cadastre ou escolha uma na aba "Paradas".',
                      bootstyle='secondary', font=('Segoe UI', 11)).pack(pady=40)
            return

        s = self.ctx.state.calcular_estatisticas(parada['id'])

        cabecalho = tb.Frame(self)
        cabecalho.pack(fill='x', pady=(0, 16))
        tb.Label(cabecalho, text=f"Resumo — {parada['nome']}", font=('Segoe UI', 16, 'bold')).pack(anchor='w')

        cards = tb.Frame(self)
        cards.pack(fill='x', pady=(0, 16))
        dados_cards = [
            (str(s['total']), 'Atividades cadastradas', 'primary'),
            (f"{s['progressoMedio']}%", 'Progresso médio', 'info'),
            (formatar_horas(s['duracaoTotalHoras']) if s['duracaoTotalHoras'] is not None else '—', 'Duração total da parada', 'success'),
            (formatar_horas(s['horasTotais']), 'Soma das durações', 'secondary'),
            (formatar_moeda(s['custoTotal']) if s['custoTotal'] > 0 else '—', 'Custo estimado de recursos', 'warning'),
        ]
        for i, (valor, rotulo, estilo) in enumerate(dados_cards):
            self._criar_card(cards, valor, rotulo, estilo).grid(row=0, column=i, sticky='nsew', padx=(0 if i == 0 else 8, 0))
            cards.columnconfigure(i, weight=1)

        colunas = tb.Frame(self)
        colunas.pack(fill='both', expand=True)
        colunas.columnconfigure(0, weight=1)
        colunas.columnconfigure(1, weight=1)

        self._painel_status(colunas, s).grid(row=0, column=0, sticky='nsew', padx=(0, 8))
        self._painel_recursos(colunas, s).grid(row=0, column=1, sticky='nsew', padx=(8, 0))

        janela = tb.Labelframe(self, text='Janela da parada', padding=14)
        janela.pack(fill='x', pady=(16, 0))
        inicio_txt = formatar_data_hora(s['inicio']) if s['inicio'] else '—'
        fim_txt = formatar_data_hora(s['fim']) if s['fim'] else '—'
        tb.Label(janela, text=f'Início mais cedo: {inicio_txt}    ·    Fim mais tarde: {fim_txt}',
                  bootstyle='secondary').pack(anchor='w')

    def _criar_card(self, parent, valor, rotulo, estilo):
        card = tb.Frame(parent, bootstyle='light', padding=16)
        tb.Label(card, text=valor, font=('Segoe UI', 22, 'bold'), bootstyle=estilo).pack(anchor='w')
        tb.Label(card, text=rotulo, bootstyle='secondary', font=('Segoe UI', 9)).pack(anchor='w')
        return card

    def _painel_status(self, parent, s):
        painel = tb.Labelframe(parent, text='Atividades por status', padding=14)
        total = s['total'] or 1
        for chave, rotulo in STATUS_LABELS.items():
            qtd = s['porStatus'].get(chave, 0)
            pct = round(qtd / total * 100) if s['total'] else 0
            linha = tb.Frame(painel)
            linha.pack(fill='x', pady=4)
            tb.Label(linha, text=rotulo, width=16, anchor='w').pack(side='left')
            barra = tb.Progressbar(linha, value=pct, maximum=100, bootstyle=STATUS_BOOTSTYLE.get(chave, 'secondary'))
            barra.pack(side='left', fill='x', expand=True, padx=8)
            tb.Label(linha, text=str(qtd), width=3, anchor='e').pack(side='left')
        return painel

    def _painel_recursos(self, parent, s):
        painel = tb.Labelframe(parent, text='Recursos por tipo (quantidade)', padding=14)
        if not s['recursosPorTipo']:
            tb.Label(painel, text='Nenhum recurso cadastrado.', bootstyle='secondary').pack(anchor='w')
            return painel
        maior = max(s['recursosPorTipo'].values()) or 1
        rotulos_tipo = {
            'mao_de_obra': 'Mão de obra', 'equipamento': 'Equipamento',
            'material': 'Material', 'servico': 'Serviço',
        }
        for tipo, qtd in s['recursosPorTipo'].items():
            linha = tb.Frame(painel)
            linha.pack(fill='x', pady=4)
            tb.Label(linha, text=rotulos_tipo.get(tipo, tipo), width=16, anchor='w').pack(side='left')
            barra = tb.Progressbar(linha, value=qtd, maximum=maior, bootstyle='primary')
            barra.pack(side='left', fill='x', expand=True, padx=8)
            tb.Label(linha, text=f'{qtd:g}', width=6, anchor='e').pack(side='left')
        return painel
