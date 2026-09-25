"""Contexto compartilhado por todas as páginas da aplicação: o estado dos
dados, a pasta de trabalho atual e utilidades de notificação (barra de
status), para não depender de variáveis globais."""

from __future__ import annotations
from pathlib import Path

from ..state import AppState


class Contexto:
    def __init__(self, root, state: AppState):
        self.root = root
        self.state = state
        self.pasta_atual: Path | None = None
        self.status_texto = None  # tk.StringVar, definido pela main_window
        self._pagina_atual = None
        self._toast_after_id = None

    def registrar_status_var(self, var):
        self.status_texto = var

    def status_base(self) -> str:
        pasta = str(self.pasta_atual) if self.pasta_atual else 'nenhuma pasta selecionada'
        return f'📁 {pasta}'

    def toast(self, mensagem: str, erro: bool = False):
        if not self.status_texto:
            return
        prefixo = '⚠ ' if erro else '✓ '
        self.status_texto.set(prefixo + mensagem)
        if self._toast_after_id:
            try:
                self.root.after_cancel(self._toast_after_id)
            except Exception:  # noqa: BLE001
                pass
        self._toast_after_id = self.root.after(4000, lambda: self.status_texto.set(self.status_base()))

    def set_pagina_atual(self, pagina):
        self._pagina_atual = pagina

    def get_pagina_atual(self):
        return self._pagina_atual
