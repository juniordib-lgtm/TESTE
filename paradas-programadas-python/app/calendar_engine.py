"""
Motor de cálculo de datas/duração baseado em um perfil de calendário.
Port fiel de calendar.js (mesma lógica, mesma simplificação proposital).

Um calendário define, para cada dia, quantas horas contam como "tempo
produtivo" da parada. Assume-se que a janela produtiva de um dia começa
sempre a partir das 00:00 e vai até `capacidade` horas depois. Isso é uma
simplificação proposital: para paradas que rodam 24h (capacidade = 24, o
mais comum), o resultado é idêntico ao tempo corrido. Para dias com
capacidade reduzida (ex.: feriado com equipe reduzida = 8h) ou dias não
úteis (capacidade = 0), o excedente do dia é simplesmente pulado.

calendario = {
    "horasPorDia": float (0-24),
    "diasUteis": [dom, seg, ter, qua, qui, sex, sab]  # booleanos
    "excecoes": {"YYYY-MM-DD": horas}
}

Índice de dia da semana segue a convenção do JavaScript (Date.getDay():
0=domingo ... 6=sábado) para que o campo `diasUteis` do JSON seja idêntico
entre a versão web e esta versão em Python.
"""

from __future__ import annotations
from datetime import datetime, timedelta
import uuid

MAX_ITER = 200_000


def date_key(dt: datetime) -> str:
    return dt.strftime('%Y-%m-%d')


def _dia_semana_js(dt: datetime) -> int:
    """Converte datetime.weekday() (0=segunda) para a convenção JS (0=domingo)."""
    return (dt.weekday() + 1) % 7


def capacidade_do_dia(dt: datetime, calendario: dict) -> float:
    key = date_key(dt)
    excecoes = calendario.get('excecoes') or {}
    if key in excecoes:
        return float(excecoes[key])
    dias_uteis = calendario.get('diasUteis') or [True] * 7
    util = bool(dias_uteis[_dia_semana_js(dt)])
    return float(calendario.get('horasPorDia', 24)) if util else 0.0


def calcular_data_fim(inicio: datetime | None, horas: float, calendario: dict) -> datetime | None:
    """Soma `horas` de tempo produtivo a partir de `inicio`, retornando a Data Fim."""
    if inicio is None or horas is None or horas < 0:
        return None

    cursor = inicio
    restante = float(horas)
    iteracoes = 0

    while restante > 1e-9 and iteracoes < MAX_ITER:
        iteracoes += 1
        capacidade = capacidade_do_dia(cursor, calendario)
        hora_do_dia = cursor.hour + cursor.minute / 60 + cursor.second / 3600

        if capacidade <= 0 or hora_do_dia >= capacidade:
            proximo_dia = datetime(cursor.year, cursor.month, cursor.day) + timedelta(days=1)
            cursor = proximo_dia
            continue

        disponivel_hoje = capacidade - hora_do_dia
        consumir = min(restante, disponivel_hoje)
        cursor = cursor + timedelta(hours=consumir)
        restante -= consumir

    return cursor


def calcular_duracao_horas(inicio: datetime | None, fim: datetime | None, calendario: dict) -> float:
    """Calcula quantas horas produtivas existem entre `inicio` e `fim`."""
    if inicio is None or fim is None or fim <= inicio:
        return 0.0

    cursor = inicio
    total = 0.0
    iteracoes = 0

    while cursor < fim and iteracoes < MAX_ITER:
        iteracoes += 1
        capacidade = capacidade_do_dia(cursor, calendario)
        hora_do_dia = cursor.hour + cursor.minute / 60 + cursor.second / 3600

        proxima_meia_noite = datetime(cursor.year, cursor.month, cursor.day) + timedelta(days=1)
        fim_segmento = min(fim, proxima_meia_noite)
        horas_no_segmento = (fim_segmento - cursor).total_seconds() / 3600

        if capacidade > hora_do_dia:
            contam = min(capacidade - hora_do_dia, horas_no_segmento)
            total += max(0.0, contam)

        cursor = fim_segmento

    return round(total, 2)


def calendario_padrao() -> dict:
    """Calendário padrão: parada rodando 24h por dia, todos os dias, sem exceções."""
    return {
        'id': str(uuid.uuid4()),
        'nome': 'Padrão 24h (todos os dias)',
        'horasPorDia': 24,
        'diasUteis': [True, True, True, True, True, True, True],
        'excecoes': {}
    }
