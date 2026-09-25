"""Aba Relatórios: os 4 relatórios imprimíveis, abertos no navegador padrão
(use "Imprimir → Salvar como PDF" do navegador para gerar o PDF)."""

from __future__ import annotations
import ttkbootstrap as tb

from .. import html_reports


class PaginaRelatorios(tb.Frame):
    def __init__(self, parent, ctx):
        super().__init__(parent, padding=20)
        self.ctx = ctx
        self._montar_esqueleto()

    def _montar_esqueleto(self):
        tb.Label(self, text='Relatórios', font=('Segoe UI', 16, 'bold')).pack(anchor='w', pady=(0, 4))
        tb.Label(self, bootstyle='secondary', text=(
            'Cada relatório abre como uma página no seu navegador padrão — use "Imprimir → '
            'Salvar como PDF" do próprio navegador para gerar o arquivo.'
        )).pack(anchor='w', pady=(0, 16))

        botoes = tb.Frame(self)
        botoes.pack(fill='x')
        opcoes = [
            ('📄 Relatório Simplificado', html_reports.relatorio_simplificado, 'relatorio-simplificado'),
            ('📋 Relatório Completo / Detalhado', html_reports.relatorio_completo, 'relatorio-completo'),
            ('📊 Relatório Gantt', html_reports.relatorio_gantt, 'relatorio-gantt'),
            ('🖼 Relatório com Imagens', html_reports.relatorio_imagens, 'relatorio-imagens'),
        ]
        for texto, fn, nome_base in opcoes:
            tb.Button(botoes, text=texto, bootstyle='outline-primary',
                      command=lambda fn=fn, nome_base=nome_base: self._gerar(fn, nome_base)).pack(
                fill='x', pady=4)

    def atualizar(self):
        pass  # conteúdo estático — nada a redesenhar quando os dados mudam

    def _gerar(self, fn, nome_base):
        parada = self.ctx.state.get_parada_ativa()
        if not parada:
            self.ctx.toast('Selecione uma parada na aba "Paradas" antes de gerar um relatório.', erro=True)
            return
        html = fn(self.ctx.state, parada)
        caminho = html_reports.abrir_no_navegador(html, nome_base)
        self.ctx.toast(f'Relatório aberto no navegador ({caminho.name}).')
