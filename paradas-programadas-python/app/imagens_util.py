"""Codificação/decodificação de imagens em data URL base64 — mesmo formato
usado pela versão web (`{"nome", "tipo", "dataUrl"}`), o que mantém o JSON
das duas versões intercambiável."""

from __future__ import annotations
import base64
import mimetypes
from pathlib import Path


def codificar_arquivo(caminho: Path) -> dict:
    caminho = Path(caminho)
    tipo = mimetypes.guess_type(caminho.name)[0] or 'application/octet-stream'
    conteudo = caminho.read_bytes()
    b64 = base64.b64encode(conteudo).decode('ascii')
    return {
        'id': None,  # preenchido pelo chamador com um uid
        'nome': caminho.name,
        'tipo': tipo,
        'dataUrl': f'data:{tipo};base64,{b64}',
    }


def decodificar_data_url(data_url: str) -> bytes:
    _, _, b64 = data_url.partition(',')
    return base64.b64decode(b64)
