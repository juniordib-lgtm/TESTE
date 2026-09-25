"""Helpers de formatação compartilhados por toda a interface e pelos relatórios."""

from __future__ import annotations
from datetime import datetime
from html import escape as escape_html  # reexportado por conveniência

from . import dates


def formatar_data_hora(iso_ou_dt) -> str:
    dt = iso_ou_dt if isinstance(iso_ou_dt, datetime) else dates.from_iso_utc(iso_ou_dt)
    if dt is None:
        return '—'
    return dt.strftime('%d/%m/%Y %H:%M')


def formatar_data(iso_ou_dt) -> str:
    dt = iso_ou_dt if isinstance(iso_ou_dt, datetime) else dates.from_iso_utc(iso_ou_dt)
    if dt is None:
        return '—'
    return dt.strftime('%d/%m/%Y')


def formatar_horas(horas) -> str:
    if horas is None:
        return '—'
    try:
        horas = float(horas)
    except (TypeError, ValueError):
        return '—'
    if horas < 24:
        return f'{round(horas, 1):g}h'
    dias = int(horas // 24)
    resto = round(horas - dias * 24, 1)
    return f'{dias}d {resto:g}h' if resto > 0 else f'{dias}d'


def formatar_moeda(valor) -> str:
    try:
        valor = float(valor)
    except (TypeError, ValueError):
        return '—'
    return f"R$ {valor:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')
