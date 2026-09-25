"""
Geração dos relatórios imprimíveis (Simplificado, Completo/Detalhado,
Gantt e Com Imagens) como páginas HTML autocontidas.

Por quê HTML em vez de gerar PDF diretamente? Para manter a aplicação sem
nenhuma dependência pesada (reportlab, weasyprint, etc.) — a página é
aberta no navegador padrão do sistema (`webbrowser.open`) e o usuário usa
"Imprimir → Salvar como PDF" do próprio navegador, exatamente o mesmo
mecanismo que a versão web deste sistema já usa.
"""

from __future__ import annotations
import tempfile
import webbrowser
from datetime import datetime, timedelta
from html import escape as esc
from pathlib import Path

from . import dates
from .formatting import formatar_data_hora, formatar_horas, formatar_moeda
from .state import STATUS_LABELS, STATUS_CORES, STATUS_CORES_CLARAS, TIPOS_RECURSO, AppState

CSS = """
body { font-family: -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; color:#1e293b; margin:0; background:#fff; }
.pagina { max-width: 980px; margin: 0 auto; padding: 24px; }
h2 { margin: 0 0 2px; }
h3 { font-weight:400; color:#64748b; margin: 0 0 10px; }
h4 { margin: 0 0 4px; }
.text-muted { color:#64748b; }
table { border-collapse: collapse; width:100%; font-size:12.5px; }
th, td { text-align:left; padding:6px; border-bottom:1px solid #e2e8f0; }
th { background:#f8fafc; border-bottom:2px solid #e2e8f0; }
.badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; font-weight:600; }
.imagens-grid { display:flex; flex-wrap:wrap; gap:10px; margin-top:8px; }
.imagem-item { text-align:center; }
.imagem-item img { width:170px; height:170px; object-fit:cover; border-radius:6px; border:1px solid #e2e8f0; }
.imagem-item .legenda { font-size:11px; color:#64748b; max-width:170px; margin-top:2px; }
.toolbar { text-align:right; margin-bottom:14px; }
.toolbar button { background:#2563eb; color:#fff; border:none; border-radius:6px; padding:8px 16px; font-size:13px; cursor:pointer; }
hr { border:none; border-top:1px solid #e2e8f0; margin:14px 0; }
.bloco-atividade { padding:12px 0; border-bottom:1px solid #e2e8f0; page-break-inside: avoid; }
.gantt-wrap { overflow-x:auto; }
.gantt-grid { display:grid; min-width:100%; }
.gantt-row { display:grid; grid-template-columns:240px 1fr; border-bottom:1px solid #e2e8f0; align-items:stretch; }
.gantt-row.header { background:#f8fafc; font-weight:700; font-size:11px; }
.gantt-label { padding:6px 8px; border-right:1px solid #e2e8f0; font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.gantt-timeline { position:relative; min-height:30px; }
.gantt-daycols { position:absolute; inset:0; display:flex; }
.gantt-daycol { border-right:1px solid #f1f5f9; flex-shrink:0; }
.gantt-daycol.weekend { background:#f8fafc; }
.gantt-header-cell { flex-shrink:0; text-align:center; padding:4px 2px; border-right:1px solid #e2e8f0; font-size:11px; overflow:hidden; }
.gantt-bar { position:absolute; top:6px; height:18px; border-radius:4px; color:#fff; font-size:10px; padding:0 6px; display:flex; align-items:center; overflow:hidden; white-space:nowrap; }
@media print { .toolbar { display:none; } }
"""

TOOLBAR = '<div class="toolbar"><button onclick="window.print()">🖨 Imprimir / Salvar PDF</button></div>'


def _pagina(titulo: str, corpo: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="UTF-8"><title>{esc(titulo)}</title>
<style>{CSS}</style></head>
<body><div class="pagina">{TOOLBAR}{corpo}</div></body></html>"""


def _cabecalho(titulo: str, state: AppState, parada: dict) -> str:
    s = state.calcular_estatisticas(parada['id'])
    return f"""
      <h2>{esc(titulo)}</h2>
      <h3>{esc(parada['nome'])}</h3>
      <p class="text-muted">Local: {esc(parada.get('local') or '—')} · Gerado em {formatar_data_hora(datetime.now())}</p>
      <p class="text-muted">Período: {formatar_data_hora(s['inicio']) if s['inicio'] else '—'} até {formatar_data_hora(s['fim']) if s['fim'] else '—'} ·
      Duração total: {formatar_horas(s['duracaoTotalHoras']) if s['duracaoTotalHoras'] is not None else '—'} ·
      {s['total']} atividade(s) · progresso médio {s['progressoMedio']}%</p>
      <hr>
    """


def _badge(status: str) -> str:
    cor = STATUS_CORES.get(status, '#334155')
    fundo = STATUS_CORES_CLARAS.get(status, '#e2e8f0')
    return f'<span class="badge" style="background:{fundo}; color:{cor};">{esc(STATUS_LABELS.get(status, status))}</span>'


# ---------------- Relatório Simplificado ----------------

def relatorio_simplificado(state: AppState, parada: dict) -> str:
    linhas = state.lista_achatada(parada['id'])
    corpo_linhas = []
    for a in linhas:
        prefixo = ('　　' * a['nivel']) + ('↳ ' if a['nivel'] > 0 else '')
        corpo_linhas.append(f"""<tr>
          <td>{prefixo}{esc(a['nome'])}</td>
          <td>{esc(a.get('numeroOS') or '—')}</td>
          <td>{esc(a.get('responsavel') or '—')}</td>
          <td>{_badge(a['status'])}</td>
          <td>{formatar_data_hora(a.get('dataInicio'))}</td>
          <td>{formatar_data_hora(a.get('dataFim'))}</td>
          <td>{formatar_horas(a.get('duracaoHoras'))}</td>
          <td>{formatar_data_hora(a['inicioReal']) if a.get('inicioReal') else '—'}</td>
          <td>{formatar_data_hora(a['fimReal']) if a.get('fimReal') else '—'}</td>
          <td>{a.get('progresso') or 0}%</td>
        </tr>""")
    tabela = f"""<table><thead><tr>
        <th>Atividade</th><th>OS</th><th>Responsável</th><th>Status</th>
        <th>Início plan.</th><th>Fim plan.</th><th>Duração</th>
        <th>Início real</th><th>Fim real</th><th>Progr.</th>
      </tr></thead><tbody>{''.join(corpo_linhas) or '<tr><td colspan="10">Nenhuma atividade cadastrada.</td></tr>'}</tbody></table>"""
    return _pagina('Relatório Simplificado', _cabecalho('Relatório Simplificado', state, parada) + tabela)


# ---------------- Relatório Completo / Detalhado ----------------

def relatorio_completo(state: AppState, parada: dict) -> str:
    arvore = state.arvore_atividades(parada['id'])

    def bloco(a: dict, nivel: int) -> str:
        recursos = a.get('recursos') or []
        imagens = a.get('imagens') or []
        custo = sum((r.get('quantidade') or 0) * (r.get('custoUnitario') or 0) for r in recursos)
        pred = state.get_atividade(a.get('predecessoraId')) if a.get('predecessoraId') else None
        sucessoras = state.sucessoras_diretas(a['id'])

        tabela_recursos = ''
        if recursos:
            linhas_r = ''.join(f"""<tr>
                <td>{esc(r.get('nome') or '—')}</td>
                <td>{esc(TIPOS_RECURSO.get(r.get('tipo'), r.get('tipo') or ''))}</td>
                <td>{r.get('quantidade') if r.get('quantidade') is not None else '—'}</td>
                <td>{esc(r.get('unidade') or '—')}</td>
                <td>{formatar_moeda(r['custoUnitario']) if r.get('custoUnitario') else '—'}</td>
              </tr>""" for r in recursos)
            tabela_recursos = (
                '<table style="font-size:12px; margin-top:6px;"><thead><tr>'
                '<th>Recurso</th><th>Tipo</th><th>Qtd</th><th>Unid.</th><th>Custo unit.</th>'
                f'</tr></thead><tbody>{linhas_r}</tbody></table>'
            )
            if custo > 0:
                tabela_recursos += f'<p class="text-muted" style="margin-top:4px;">Custo estimado dos recursos: {formatar_moeda(custo)}</p>'
        else:
            tabela_recursos = '<p class="text-muted" style="margin-top:6px;">Nenhum recurso cadastrado.</p>'

        galeria = ''
        if imagens:
            itens = ''.join(
                f'<div class="imagem-item"><img src="{im["dataUrl"]}" alt="{esc(im.get("nome") or "")}"></div>'
                for im in imagens
            )
            galeria = f'<div class="imagens-grid">{itens}</div>'

        real = ''
        if a.get('inicioReal'):
            dur_real = state.duracao_real_horas(a)
            fim_txt = formatar_data_hora(a['fimReal']) if a.get('fimReal') else 'em andamento'
            extra = f' ({formatar_horas(dur_real)})' if a.get('fimReal') else ''
            real = f'<p class="text-muted" style="margin:2px 0;">Execução real: {formatar_data_hora(a["inicioReal"])} → {fim_txt}{extra}</p>'

        dep = ''
        if pred:
            defasagem = a.get('defasagemHoras')
            sufixo = f' (+{defasagem}h)' if defasagem else ''
            dep += f'<p class="text-muted" style="margin:2px 0;">🔗 Predecessora: {esc(pred["nome"])}{sufixo}</p>'
        if sucessoras:
            dep += f'<p class="text-muted" style="margin:2px 0;">➜ Sucessoras: {", ".join(esc(s["nome"]) for s in sucessoras)}</p>'

        html_bloco = f"""
        <div class="bloco-atividade" style="margin-left:{nivel * 22}px;">
          <h4>{'↳ ' if nivel > 0 else ''}{esc(a['nome'])}{f" <span class=\"text-muted\" style=\"font-weight:400;\">(OS {esc(a['numeroOS'])})</span>" if a.get('numeroOS') else ''} {_badge(a['status'])}</h4>
          <p class="text-muted" style="margin:2px 0;">Responsável: {esc(a.get('responsavel') or '—')} · Área: {esc(a.get('area') or '—')}</p>
          <p class="text-muted" style="margin:2px 0;">Planejado: {formatar_data_hora(a.get('dataInicio'))} → {formatar_data_hora(a.get('dataFim'))} ·
          Duração: {formatar_horas(a.get('duracaoHoras'))} · Progresso: {a.get('progresso') or 0}%</p>
          {real}
          {dep}
          {f'<p style="margin:6px 0;">{esc(a["descricao"])}</p>' if a.get('descricao') else ''}
          {tabela_recursos}
          {galeria}
        </div>"""
        return html_bloco + ''.join(bloco(s, nivel + 1) for s in a.get('subAtividades') or [])

    corpo = ''.join(bloco(a, 0) for a in arvore) or '<p>Nenhuma atividade cadastrada.</p>'
    return _pagina('Relatório Completo e Detalhado', _cabecalho('Relatório Completo e Detalhado', state, parada) + corpo)


# ---------------- Relatório com Imagens ----------------

def relatorio_imagens(state: AppState, parada: dict) -> str:
    achatada = state.lista_achatada(parada['id'])
    com_imagem = [a for a in achatada if a.get('imagens')]
    sem_imagem = [a for a in achatada if not a.get('imagens')]

    blocos = []
    for a in com_imagem:
        itens = ''.join(
            f'<div class="imagem-item"><img src="{im["dataUrl"]}" alt="{esc(im.get("nome") or "")}">'
            f'<div class="legenda">{esc(im.get("nome") or "")}</div></div>'
            for im in a['imagens']
        )
        blocos.append(f"""
        <div class="bloco-atividade" style="margin-left:{a['nivel'] * 22}px;">
          <h4>{'↳ ' if a['nivel'] > 0 else ''}{esc(a['nome'])} {_badge(a['status'])}</h4>
          <p class="text-muted" style="margin:2px 0;">Responsável: {esc(a.get('responsavel') or '—')} ·
          Planejado: {formatar_data_hora(a.get('dataInicio'))} → {formatar_data_hora(a.get('dataFim'))}</p>
          <div class="imagens-grid">{itens}</div>
        </div>""")

    rodape = ''
    if sem_imagem:
        nomes = ', '.join(esc(a['nome']) for a in sem_imagem)
        rodape = f'<p class="text-muted" style="margin-top:12px;">Sem imagens anexadas: {nomes}.</p>'

    corpo = ''.join(blocos) or '<p>Nenhuma atividade possui imagens anexadas.</p>'
    return _pagina('Relatório com Imagens', _cabecalho('Relatório com Imagens', state, parada) + corpo + rodape)


# ---------------- Relatório Gantt ----------------

def _dias_entre(inicio: datetime, fim: datetime) -> list[datetime]:
    dias = []
    cursor = datetime(inicio.year, inicio.month, inicio.day)
    limite = datetime(fim.year, fim.month, fim.day)
    while cursor <= limite:
        dias.append(cursor)
        cursor += timedelta(days=1)
    return dias


def relatorio_gantt(state: AppState, parada: dict) -> str:
    from datetime import timedelta

    linhas = [a for a in state.lista_achatada(parada['id']) if a.get('dataInicio') and a.get('dataFim')]
    if not linhas:
        corpo = _cabecalho('Relatório Gantt', state, parada) + '<p>Nenhuma atividade com datas definidas.</p>'
        return _pagina('Relatório Gantt', corpo)

    range_inicio = min(dates.from_iso_utc(a['dataInicio']) for a in linhas) - timedelta(hours=12)
    range_fim = max(dates.from_iso_utc(a['dataFim']) for a in linhas) + timedelta(hours=12)
    dias = _dias_entre(range_inicio, range_fim)
    col_w = 46
    hoje = datetime.now().strftime('%Y-%m-%d')

    daycols = ''.join(
        f'<div class="gantt-daycol{" weekend" if d.weekday() >= 5 else ""}" style="width:{col_w}px"></div>'
        for d in dias
    )
    header_cells = ''.join(
        f'<div class="gantt-header-cell" style="width:{col_w}px">{d.strftime("%d/%m")}</div>' for d in dias
    )
    total_w = len(dias) * col_w
    ms_por_px = (range_fim - range_inicio).total_seconds() * 1000 / total_w

    def barra_style(ini, fim):
        left = (ini - range_inicio).total_seconds() * 1000 / ms_por_px
        largura = max(6, (fim - ini).total_seconds() * 1000 / ms_por_px)
        return f'left:{left:.1f}px; width:{largura:.1f}px;'

    linhas_html = []
    for a in linhas:
        ini = dates.from_iso_utc(a['dataInicio'])
        fim = dates.from_iso_utc(a['dataFim'])
        cor = STATUS_CORES.get(a['status'], '#2563eb')
        nivel = a['nivel']
        linhas_html.append(f"""
        <div class="gantt-row">
          <div class="gantt-label" style="padding-left:{8 + nivel * 16}px">{'↳ ' if nivel > 0 else ''}{esc(a['nome'])}</div>
          <div class="gantt-timeline" style="width:{total_w}px">
            <div class="gantt-daycols">{daycols}</div>
            <div class="gantt-bar" style="{barra_style(ini, fim)} background:{cor};">{esc(a['nome'])}</div>
          </div>
        </div>""")

    grid = f"""<div class="gantt-wrap"><div class="gantt-grid">
      <div class="gantt-row header">
        <div class="gantt-label">Atividade</div>
        <div class="gantt-timeline" style="width:{total_w}px; min-height:0;"><div style="display:flex;">{header_cells}</div></div>
      </div>
      {''.join(linhas_html)}
    </div></div>"""

    return _pagina('Relatório Gantt', _cabecalho('Relatório Gantt', state, parada) + grid)


# ---------------- Abertura no navegador ----------------

def abrir_no_navegador(html: str, nome_base: str) -> Path:
    pasta_tmp = Path(tempfile.gettempdir()) / 'paradas-programadas-relatorios'
    pasta_tmp.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    caminho = pasta_tmp / f'{nome_base}-{ts}.html'
    caminho.write_text(html, encoding='utf-8')
    webbrowser.open(caminho.as_uri())
    return caminho
