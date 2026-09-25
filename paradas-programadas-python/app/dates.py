"""
Conversão de datas entre o horário local (usado internamente pela aplicação
e exibido na interface) e strings ISO 8601 em UTC (usadas para gravar no
JSON) — no mesmo formato que `Date.prototype.toISOString()` produz em
JavaScript (ex.: "2026-03-01T11:00:00.000Z").

Isso existe por um motivo específico: manter o arquivo `dados-paradas.json`
desta versão em Python **intercambiável** com o da versão web do mesmo
sistema (paradas-programadas/). As duas guardam as datas exatamente no
mesmo formato, então um backup exportado por uma abre normalmente na outra.
"""

from __future__ import annotations
from datetime import datetime, timezone


def agora_iso_utc() -> str:
    return to_iso_utc(datetime.now())


def to_iso_utc(dt_local: datetime | None) -> str | None:
    """Converte um datetime "ingênuo" (sem timezone), presumido como
    horário local da máquina, para uma string ISO 8601 em UTC com 'Z'."""
    if dt_local is None:
        return None
    aware_utc = dt_local.astimezone(timezone.utc)
    ms = aware_utc.microsecond // 1000
    return aware_utc.strftime('%Y-%m-%dT%H:%M:%S') + f'.{ms:03d}Z'


def from_iso_utc(iso_str: str | None) -> datetime | None:
    """Converte uma string ISO 8601 em UTC de volta para um datetime
    "ingênuo" em horário local — pronto para uso pelo motor de calendário
    e para exibição nos campos da interface."""
    if not iso_str:
        return None
    s = iso_str.strip()
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        aware = datetime.fromisoformat(s)
    except ValueError:
        return None
    if aware.tzinfo is None:
        # string sem timezone: trata como já sendo horário local
        return aware
    return aware.astimezone().replace(tzinfo=None)
