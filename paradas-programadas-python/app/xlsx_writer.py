"""
Gerador de planilhas .xlsx sem nenhuma dependência externa (só a biblioteca
padrão do Python — `zipfile` cuida do formato ZIP, e aqui só é preciso
montar o XML mínimo do OOXML). Mesma técnica usada na versão web
(js/xlsx-writer.js), reaproveitada aqui de forma mais simples porque o
`zipfile` do Python já resolve o que lá precisou ser escrito à mão (CRC32,
cabeçalhos locais/centrais, etc.).
"""

from __future__ import annotations
import zipfile
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape


def _col_letter(n: int) -> str:
    """0-indexado -> 'A', 'B', ..., 'Z', 'AA', ..."""
    n += 1
    s = ''
    while n > 0:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


def _celula_xml(valor, col_idx: int, row_idx: int) -> str:
    ref = f'{_col_letter(col_idx)}{row_idx}'
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return f'<c r="{ref}"><v>{valor}</v></c>'
    texto = '' if valor is None else str(valor)
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{xml_escape(texto)}</t></is></c>'


def _sheet_xml(colunas: list[str], linhas: list[list]) -> str:
    partes = [f'<row r="1">{"".join(_celula_xml(c, i, 1) for i, c in enumerate(colunas))}</row>']
    for li, linha in enumerate(linhas):
        r = li + 2
        partes.append(f'<row r="{r}">{"".join(_celula_xml(v, i, r) for i, v in enumerate(linha))}</row>')
    largura = max([10] + [min(45, len(str(c)) + 4) for c in colunas])
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<cols><col min="1" max="{max(1, len(colunas))}" width="{largura}" customWidth="1"/></cols>'
        f'<sheetData>{"".join(partes)}</sheetData>'
        '</worksheet>'
    )


def _nome_sheet_valido(nome: str, indice: int) -> str:
    for ch in ':\\/?*[]':
        nome = nome.replace(ch, ' ')
    nome = nome.strip() or f'Planilha{indice + 1}'
    return nome[:31]


def gerar_bytes(planilhas: list[dict]) -> bytes:
    """planilhas: [{'nome': 'Atividades', 'colunas': [...], 'linhas': [[...], ...]}]"""
    nomes = [_nome_sheet_valido(p['nome'], i) for i, p in enumerate(planilhas)]

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + ''.join(
            f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            for i in range(len(planilhas))
        )
        + '</Types>'
    )

    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="xl/workbook.xml"/></Relationships>'
    )

    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets>'
        + ''.join(f'<sheet name="{xml_escape(nome)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, nome in enumerate(nomes))
        + '</sheets></workbook>'
    )

    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + ''.join(
            f'<Relationship Id="rId{i + 1}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'Target="worksheets/sheet{i + 1}.xml"/>'
            for i in range(len(planilhas))
        )
        + '</Relationships>'
    )

    buf = BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', content_types)
        z.writestr('_rels/.rels', root_rels)
        z.writestr('xl/workbook.xml', workbook)
        z.writestr('xl/_rels/workbook.xml.rels', workbook_rels)
        for i, p in enumerate(planilhas):
            z.writestr(f'xl/worksheets/sheet{i + 1}.xml', _sheet_xml(p['colunas'], p['linhas']))

    return buf.getvalue()


def salvar(planilhas: list[dict], caminho: Path):
    caminho = Path(caminho)
    if caminho.suffix.lower() != '.xlsx':
        caminho = caminho.with_suffix('.xlsx')
    caminho.write_bytes(gerar_bytes(planilhas))
    return caminho
