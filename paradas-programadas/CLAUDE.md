# Paradas Programadas — contexto para sessões futuras do Claude Code

Este arquivo existe para que qualquer sessão futura do Claude Code aberta
neste repositório já tenha o contexto do que foi construído aqui, sem
precisar re-explorar tudo do zero. Leia também `README.md` (documentação
voltada ao usuário final).

## O que é

Sistema web 100% local (sem backend, sem build step, sem dependências
externas) para planejar e acompanhar **paradas programadas de manutenção**
(shutdowns/turnarounds industriais). Pedido original do usuário e todas as
extensões feitas depois estão registradas no histórico de commits desta
pasta na branch `claude/scheduled-downtime-system-sy0utn`
([PR #1](https://github.com/juniordib-lgtm/TESTE/pull/1)).

Este projeto vive dentro de um repositório (`juniordib-lgtm/TESTE`) cujo
conteúdo original é um app Android não relacionado ("Zap Agendado", na raiz
do repo) — os dois projetos coexistem sem se misturar; tudo relativo a
paradas programadas fica isolado em `paradas-programadas/`.

## Arquitetura

- **Vanilla JS, sem módulos ES** (`<script>` normais, nesta ordem no
  `index.html`) — proposital, para funcionar tanto abrindo `index.html`
  direto (`file://`) quanto por servidor local, sem CORS de módulos.
- **Sem build step, sem npm, sem frameworks.** Tudo é HTML/CSS/JS puro.
- Módulos (em `js/`), na ordem de carregamento:
  `utils.js` → `calendar.js` → `storage.js` → `state.js` → `xlsx-writer.js`
  → `ui-imagens.js` → `ui-paradas-calendarios.js` → `ui-atividades.js` →
  `ui-tabela.js` → `ui-gantt.js` → `ui-resumo.js` → `ui-relatorios.js` →
  `main.js`.
- Cada módulo de UI é uma IIFE que expõe um objeto global (`UIAtividades`,
  `UIGantt`, etc.) com `render()` + funções específicas.

## Modelo de dados (`state.js`)

Objeto único `data` persistido inteiro a cada mudança:
```
{ version, paradaAtivaId, paradas[], calendarios[], atividades[] }
```
- **parada**: `{id, nome, local, descricao, status, calendarioId, criadoEm}`
- **calendario**: `{id, nome, horasPorDia, diasUteis[7], excecoes:{ "YYYY-MM-DD": horas }}`
  — define quanto de cada dia conta como "tempo produtivo" (ver
  `calendar.js`). Simplificação proposital: a janela produtiva de cada dia
  sempre começa à meia-noite.
- **atividade** (também usada para sub-atividade, via `parentId`):
  `{id, paradaId, parentId, nome, descricao, responsavel, area, status,
  progresso, dataInicio, duracaoHoras, dataFim, inicioReal, fimReal,
  predecessoraId, defasagemHoras, imagens[], recursos[], ordem}`.
  Imagens e recursos ficam **embutidos no próprio objeto** (não são
  coleções separadas) — imagens em base64 (`dataUrl`).

### Motor de datas (`calendar.js`)
`calcularDataFim(inicio, horas, calendario)` e
`calcularDuracaoHoras(inicio, fim, calendario)` — andam hora a hora
respeitando a capacidade diária do calendário. Ver comentário no topo do
arquivo para o racional da simplificação.

### Predecessora/sucessora (`state.recalcularProgramacao`)
Se uma atividade tem `predecessoraId`, sua `dataInicio` é **sempre**
derivada de `predecessora.dataFim + defasagemHoras` (o usuário não digita
mais esse campo — vira `readonly` no form). `recalcularProgramacao(paradaId)`
percorre todas as atividades em profundidade (predecessora antes de
sucessora, com memoização e proteção contra ciclo) e é chamada sempre que:
uma atividade é salva/excluída, o calendário de uma parada muda, ou o
calendário atribuído a uma parada muda. `cadeiaSucessoras(id)` é usada para
filtrar o `<select>` de predecessora e impedir referência circular.

### Hierarquia sem limite de profundidade
Sub-atividade pode ter sua própria sub-atividade, em qualquer nível — não
há campo/flag de "nível máximo", `arvoreAtividades`/`listaAchatada` já eram
recursivas desde o início. A única coisa que antes limitava a 1 nível era o
`<select name="parentId">` do formulário, que só listava atividades de
topo; agora lista `State.listaAchatada(paradaId)` inteira (com indentação
visual por `nivel`), filtrando com `cadeiaDescendentes(id)` (análogo ao
`cadeiaSucessoras` das predecessoras) para impedir que uma atividade vire
sub-atividade de algo que já é seu próprio descendente. A indentação visual
(margin/padding proporcional a `nivel`) é aplicada inline em
`ui-atividades.js` (lista) e `ui-gantt.js` (rótulos), já que o `nivel` não
tem teto fixo.

### Ordenação
`listarAtividadesDaParada` ordena por `dataInicio` (não por ordem de
cadastro). `arvoreAtividades`/`listaAchatada` mantêm cada sub-atividade
agrupada logo abaixo da atividade-mãe, preservando ordem cronológica dentro
de cada nível — é assim que a listagem, o Gantt e os relatórios exibem as
atividades.

## Persistência (`storage.js`)

- **IndexedDB** é o armazenamento primário, sempre disponível (funciona
  mesmo abrindo por `file://`).
- **File System Access API** (opcional, Chromium): grava
  `dados-paradas.json` numa pasta escolhida pelo usuário.
  - `folderHandle` = pasta ativa nesta sessão (permissão concedida).
  - `pastaArmazenadaHandle` = pasta lembrada entre sessões (guardada no
    IndexedDB via `idb-keyval`-style store).
  - Botão **"📁 Pasta"** → `conectarPastaSalva()`: reconecta a pasta já
    lembrada com 1 clique (sem abrir seletor novo).
  - Botão **"🔁 Trocar pasta"** (só aparece quando já há pasta lembrada) →
    `escolherPasta()`: única ação que abre `showDirectoryPicker` de novo.
  - Isso foi um pedido explícito do usuário: "depois de definido o
    diretório, só deve pedir seleção de novo se eu quiser trocar".
- Exportar/Importar JSON como alternativa manual sempre disponível
  (funciona em qualquer navegador).

## Excel sem dependências (`xlsx-writer.js`)

Gerador de `.xlsx` **puro JS, zero bibliotecas externas** (importante:
sistema tem que continuar 100% offline/local). Implementa um ZIP mínimo
(armazenamento sem compressão, CRC32 manual) + XML OOXML mínimo (sheets com
`inlineStr`, sem `sharedStrings.xml`). Validado abrindo com
`python3 -m zipfile` e com `openpyxl` durante o desenvolvimento — abre
corretamente no Excel/LibreOffice/Google Sheets.

## Views / abas

Resumo · Paradas · Calendários · Atividades · Tabela · Gantt · Relatórios
(Simplificado, Completo/Detalhado, Gantt, Com Imagens — os 4 relatórios são
imprimíveis via `window.print()`, com CSS `@media print` mostrando apenas
`.view.active`).

- **Gantt** (`ui-gantt.js`): barra sólida = planejado, barra tracejada
  abaixo = execução real (`inicioReal`/`fimReal`). `construirHtmlGantt` é
  reaproveitado pelo Relatório Gantt. Zoom em 3 granularidades (select
  `#gantt-zoom`): `semana`/`dia` usam colunas por dia (`diasEntre`,
  larguras diferentes); `hora` usa colunas por hora (`horasEntre`) com
  cabeçalho de duas linhas (`headerHorasHtml`: linha de dia agrupador +
  linha de hora). O posicionamento das barras (`barraStyle`) é sempre
  proporcional a milissegundos reais / largura total em pixels, então
  funciona igual nas três granularidades sem lógica especial.
- **Galeria de imagens** (`ui-imagens.js`): overlay **próprio**, fora do
  `Modal` genérico (`#modal-overlay`), para poder abrir por cima do
  formulário de atividade sem destruí-lo (bug real encontrado e corrigido
  durante o desenvolvimento).

## Como testar mudanças

Não há suite de testes automatizada formal. O padrão usado durante todo o
desenvolvimento foi **Playwright headless** ad-hoc (Chromium pré-instalado
em `/opt/pw-browsers/chromium`, biblioteca global em
`/opt/node22/lib/node_modules/playwright`), abrindo `index.html` via
`file://` e exercitando os fluxos na UI de verdade, checando
`console.error`/`pageerror`. Vale o mesmo padrão para validar futuras
mudanças antes de dar como concluído. `node --check js/*.js` para sintaxe
rápida antes disso.

## Convenções

- Todo o código/UI é em **português (pt-BR)**, nomes de função/variável
  incluídos — manter consistência.
- Sem comentários redundantes; só onde há uma decisão não óbvia (ver
  exemplos em `calendar.js` e `storage.js`).
- CSS: tokens em `:root` no topo de `style.css`.

## Histórico de pedidos (para não perder o fio)

1. Pedido inicial: sistema completo (paradas, calendário, atividades/sub
   com imagens, recursos, cálculo automático de data/duração, tabela,
   Gantt, resumo, relatórios simplificado/completo/Gantt).
2. Adicionado depois: Início/Fim real por atividade, exportar Excel,
   Relatório com Imagens, botão de pré-visualizar imagens (lightbox),
   pasta lembrada com reconexão em 1 clique + "Trocar pasta" separado.
3. Adicionado depois: atividades ordenadas por data/hora com sub-atividade
   agrupada sob a atividade-mãe.
4. Adicionado depois: predecessora/sucessora com recálculo automático em
   cascata (o pedido que motivou a criação deste `CLAUDE.md`).

Ao continuar este projeto, prefira estender esses módulos existentes a
criar paralelos novos, e mantenha o princípio raiz: **tudo roda local, sem
servidor obrigatório, sem dependências externas baixadas em tempo de
execução**.
