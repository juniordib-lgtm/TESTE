# Paradas Programadas (Python) — contexto para sessões futuras do Claude Code

Leia também `README.md` (documentação para o usuário) e, se for mexer em
ambas as versões, `../paradas-programadas/CLAUDE.md` (a versão web irmã
deste sistema — mesmo domínio, mesmo formato de JSON).

## Origem

Esta é uma **reescrita em Python** do sistema `paradas-programadas/`
(HTML/CSS/JS puro, ver seu próprio CLAUDE.md), pedida explicitamente pelo
usuário ("transforme esse sistema de paradas em python"), com melhorias
subsequentes pedidas na mesma leva: interface visual moderna
(ttkbootstrap) e um campo opcional de "Número da OS" por atividade.

**Decisão central de design**: o JSON gravado em disco usa **exatamente os
mesmos nomes de campo e o mesmo formato de data** (ISO 8601 UTC, tipo
`"2026-03-01T11:00:00.000Z"`) que a versão web. Isso foi proposital — os
arquivos `dados-paradas.json` das duas versões são intercambiáveis. Ver
`app/dates.py` para a conversão local↔UTC (usa `datetime.astimezone()`,
sem depender de bibliotecas de timezone externas).

## Arquitetura

Diferente da versão web (tudo em `<script>` globais), aqui é um pacote
Python normal:

```
app/
├── dates.py            conversão de data local ↔ ISO UTC
├── calendar_engine.py  motor de cálculo (port fiel de calendar.js)
├── state.py             AppState: CRUD + cascata de predecessoras + hierarquia
├── storage.py            pasta de trabalho, config, import/export JSON
├── xlsx_writer.py         gerador .xlsx via zipfile (stdlib) — sem libs externas
├── html_reports.py        os 4 relatórios como HTML (abertos via webbrowser.open)
├── formatting.py           formatação pt-BR de data/hora/moeda
├── imagens_util.py         base64 <-> arquivo de imagem
└── ui/                     Tkinter + ttkbootstrap
    ├── theme.py             tema "flatly", cores, STATUS_BOOTSTYLE
    ├── context.py            Contexto: state + pasta_atual + toast, compartilhado
    ├── dialogs.py             CampoDataHora, GaleriaImagens, área rolável
    ├── main_window.py         JanelaPrincipal: menu, sidebar, roteamento de páginas
    └── tab_*.py                uma página por aba (mesmo recorte da versão web)
```

`main.py` é o ponto de entrada; verifica `ttkbootstrap` antes de importar
qualquer coisa de `app.ui` e mostra um erro amigável (messagebox) se faltar
— nunca deixa estourar um traceback cru pro usuário final.

### `AppState` (`state.py`)

Port quase linha-a-linha de `state.js`: mesmos métodos (em português,
`snake_case`), mesma lógica de `recalcular_programacao` (cascata de
predecessoras, com proteção contra ciclo via pilha de recursão) e
`cadeia_descendentes`/`cadeia_sucessoras` (idem, para a hierarquia de
sub-atividades ilimitada). `AppState.data` é sempre um `dict` puro,
pronto pra `json.dump()` — sem passo de serialização separado.

Dois hooks (`on_erro`, `on_persist`) desacoplam `AppState` de Tkinter e de
disco: quem liga isso é `main_window.py` (`on_persist` agenda um
autosave debounced via `root.after`; `on_erro` vira um toast na barra de
status).

### UI: padrão de página

Cada `tab_*.py` expõe uma classe `Pagina*(tb.Frame)` com `__init__(parent,
ctx)` e um método `atualizar()` (sem argumentos, redesenha do zero a
partir de `ctx.state`). `main_window.py` instancia todas as páginas na
inicialização, empilhadas na mesma célula de grid (`grid(row=0, column=0,
sticky='nsew')`), e troca a visível com `.tkraise()` — o padrão clássico
de "multi-page app" em Tkinter. Toda mudança de estado (`state.on_change`)
chama `atualizar()` em **todas** as páginas, não só a visível — o dataset
típico (dezenas a poucas centenas de atividades) torna isso barato o
bastante para não precisar de invalidação seletiva.

### Formulário de atividade (`tab_atividades.abrir_form_atividade`)

É o maior/mais complexo pedaço de UI — mesmo recorte de campos que
`ui-atividades.js`: dados gerais (incluindo o `numeroOS` opcional),
datas planejadas com o mesmo toggle duração↔fim de antes
(`modo_calculo['valor']`, um dict só pra ter uma referência mutável dentro
dos closures dos widgets), sequenciamento (predecessora/defasagem, com
`cadeia_sucessoras`/`cadeia_descendentes` filtrando as opções pra evitar
ciclo), execução real, recursos (linhas dinâmicas) e imagens.

O widget `CampoDataHora` (`ui/dialogs.py`) substitui o
`<input type="datetime-local">` nativo do navegador: um
`ttkbootstrap.DateEntry` (calendário popup) + dois `Spinbox` (hora/minuto).
Ele expõe `get_datetime()`/`set_datetime()`/`set_somente_leitura()` e um
callback `on_change` — importante notar que o `DateEntry` usa o parâmetro
`date_format` (não `dateformat`) e o método `get_date()`/`set_date()` já
faz o parsing/validação sozinho; não reimplemente isso na mão.

### Gantt (`tab_gantt.py`)

Desenho customizado em dois `tk.Canvas` lado a lado (rótulos à esquerda,
fixo; linha do tempo à direita, rolável nos dois eixos), com uma
`Scrollbar` vertical compartilhada entre os dois canvases — é o
equivalente Tkinter do `position: sticky; left: 0` usado no CSS da versão
web. O posicionamento das barras é sempre proporcional a milissegundos
reais / pixels totais (`px_por_ms`), igual à versão web — funciona igual
nas três granularidades de zoom (Semana/Dia/Horas) sem lógica especial por
zoom, só muda `col_w` e a granularidade das colunas de fundo.

### Excel e relatórios

`xlsx_writer.py` gera OOXML mínimo (mesma técnica da versão web) mas usa
`zipfile` da biblioteca padrão em vez de reimplementar o formato ZIP à
mão — bem mais simples e robusto que o `xlsx-writer.js` original.

`html_reports.py` gera os 4 relatórios como HTML autocontido (CSS inline)
e abre no navegador padrão do sistema (`webbrowser.open`) — a impressão em
PDF fica por conta do "Imprimir → Salvar PDF" do próprio navegador,
exatamente como a versão web. Isso foi uma escolha deliberada para não
adicionar uma dependência pesada (`reportlab`/`weasyprint`) só para gerar
PDF.

## Como testar mudanças

Não há suite de testes formal (pytest etc.), mas o projeto foi construído
inteiro sob um regime de testes ad-hoc real, que vale reaproveitar:

1. **Lógica pura** (`dates.py`, `calendar_engine.py`, `state.py`,
   `storage.py`, `xlsx_writer.py`, `html_reports.py`): scripts Python
   diretos com `assert`, sem GUI — rápido e cobre a maior parte do risco
   de correção (cascata de predecessoras, hierarquia, cálculo de datas).
2. **GUI**: `tkinter` não vem instalado por padrão neste tipo de ambiente
   sandbox — `apt-get install -y python3-tk` resolve (o Python do
   `python3` "genérico" pode ser uma build diferente da que tem o pacote
   `python3-tk`; procure o binário certo, ex. `python3.12`, com
   `dpkg -L python3-tk | grep tkinter`). Rode sob `xvfb-run -a` (Xvfb já
   costuma estar instalado) para não precisar de display real.
3. **Testes de fluxo real**: instancie `JanelaPrincipal()`, ache widgets
   por classe (`isinstance(w, tb.Entry)` etc.) percorrendo
   `winfo_children()` recursivamente, preencha e `.invoke()` o botão
   "Salvar" de verdade — dá pra validar o caminho completo (diálogo →
   `AppState` → disco) sem mockar nada, só monkeypatchando
   `filedialog`/`messagebox`/`webbrowser.open` quando o teste não deve
   depender de interação humana ou abrir um navegador de verdade.

## Convenções

- Português em nomes de função/variável/classe, igual à versão web.
- `from __future__ import annotations` no topo de todo módulo novo (permite
  `dict | None` etc. mesmo em Python um pouco mais antigo).
- Sem comentários redundantes — só onde há uma decisão não óbvia (mesmo
  princípio da versão web).
