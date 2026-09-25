#!/usr/bin/env python3
"""Ponto de entrada do Paradas Programadas (versão desktop em Python).

Uso:  python3 main.py
"""

import sys


def _erro_dependencia(nome_pacote: str, detalhe: str):
    mensagem = (
        f'Não foi possível iniciar: falta instalar "{nome_pacote}".\n\n'
        f'No terminal, rode:\n    pip install -r requirements.txt\n\n'
        f'Detalhe técnico: {detalhe}'
    )
    print(mensagem, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror('Paradas Programadas — dependência ausente', mensagem)
    except Exception:  # noqa: BLE001 — ambiente sem display algum; a mensagem no terminal já foi impressa
        pass
    sys.exit(1)


def main():
    try:
        import ttkbootstrap  # noqa: F401
    except ImportError as e:
        _erro_dependencia('ttkbootstrap', str(e))
        return

    from app.ui.main_window import JanelaPrincipal
    janela = JanelaPrincipal()
    janela.run()


if __name__ == '__main__':
    main()
