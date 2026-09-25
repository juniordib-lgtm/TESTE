# Paradas Programadas (versão Python / desktop)

Versão em Python do sistema de planejamento de paradas programadas de manutenção — um aplicativo de **desktop nativo** (Tkinter + [ttkbootstrap](https://ttkbootstrap.readthedocs.io/), com visual moderno de sistema de gestão de manutenção), em vez de rodar no navegador.

Roda inteiramente no seu computador: sem servidor, sem internet, sem conta. Os dados ficam salvos numa pasta de trabalho que você escolhe, em um único arquivo `dados-paradas.json` — legível, editável e **no mesmo formato** usado pela [versão web deste sistema](../paradas-programadas/), então um backup de uma abre normalmente na outra.

## Como instalar e rodar

Requer **Python 3.10 ou mais novo** ([python.org](https://www.python.org/downloads/) — no instalador do Windows, marque "Add python.exe to PATH").

**Windows:** dê duplo clique em `scripts/iniciar-windows.bat`.
**Mac/Linux:** rode `scripts/iniciar-mac-linux.sh` (ou `python3 main.py` diretamente).

Os dois scripts instalam as dependências na primeira vez (`pip install -r requirements.txt`) e depois abrem o programa. Se preferir fazer isso manualmente:

```bash
pip install -r requirements.txt
python3 main.py
```

### Dependências

- **[ttkbootstrap](https://pypi.org/project/ttkbootstrap/)** — obrigatória. É o que dá a aparência moderna (tema "flatly") à interface; sem ela o programa mostra um aviso claro em vez de travar.
- **[Pillow](https://pypi.org/project/Pillow/)** — recomendada. Sem ela o programa funciona normalmente, mas a pré-visualização de fotos (galeria/lightbox) fica indisponível — as imagens continuam sendo anexadas e salvas normalmente, só não são exibidas dentro do app.

Ambas são puro Python (sem compilação), instalam em segundos em Windows/Mac/Linux.

## O que o sistema tem

1. **Cadastro de Paradas** — nome, local, descrição, status e o calendário utilizado.
2. **Calendários** — perfis reutilizáveis que definem quantas horas por dia contam como "tempo produtivo" da parada, quais dias da semana são úteis e exceções (feriados, dias com capacidade reduzida).
3. **Atividades e sub-atividades, em qualquer profundidade** — cada atividade pode ter sub-atividades, que por sua vez podem ter as suas próprias sub-atividades, sem limite de níveis. Cada uma tem um campo opcional de **Número da OS** (ordem de serviço), responsável, área, descrição e imagens anexadas.
4. **Recursos por atividade** — mão de obra, equipamento, material ou serviço, com quantidade, unidade e custo unitário.
5. **Data e duração com cálculo automático** — informe a Data/Hora de Início e a Duração (em horas) que a Data/Hora Fim é calculada sozinha (respeitando o calendário da parada); também funciona ao contrário. Campos de **Início real** e **Fim real** para comparar planejado × real.
6. **Predecessora e sucessoras** — ligue uma atividade a uma predecessora (com defasagem opcional em horas) e a Data Início dela passa a ser calculada automaticamente; mudanças se propagam em cascata por toda a cadeia de dependências.
7. **Visão em Tabela** (ordenável, filtrável) **e Gantt** (zoom Semana/Dia/Horas, barra sólida para o planejado e tracejada para o real), ambas com exportação para Excel na Tabela.
8. **Resumo** — painel com cartões de estatística, progresso por status e recursos por tipo.
9. **Relatórios simplificado, completo/detalhado, Gantt e com imagens** — cada um abre como uma página no seu navegador padrão; use "Imprimir → Salvar como PDF" do navegador para gerar o PDF (mesmo mecanismo da versão web).
10. **Exportar/Importar JSON** — pelo menu Arquivo, a qualquer momento, além do salvamento automático contínuo na pasta de trabalho.

## Pasta de trabalho

Ao abrir pela primeira vez, o programa cria (ou reabre) uma pasta padrão em `~/ParadasProgramadas`. Use **Arquivo → Abrir pasta de trabalho…** para escolher outro lugar — a partir daí, essa é a pasta usada e lembrada automaticamente nas próximas vezes (guardada em `~/.paradas_programadas/config.json`).

Diferente da versão web (que depende da File System Access API do navegador e precisa pedir permissão de novo a cada sessão), aqui o acesso a arquivos é nativo: não há diálogo de permissão nenhum, a pasta é reaberta direto.

Cada alteração é salva automaticamente (gravação atômica, sem risco de corromper o arquivo se o programa fechar no meio). Use **Arquivo → Exportar backup JSON…** para gerar uma cópia adicional em qualquer lugar, e **Arquivo → Importar backup JSON…** para carregar um backup (dessa mesma versão ou da versão web) — atenção: isso substitui os dados atuais.

## Estrutura dos arquivos

```
paradas-programadas-python/
├── main.py                     ponto de entrada
├── requirements.txt
├── scripts/
│   ├── iniciar-windows.bat
│   └── iniciar-mac-linux.sh
└── app/
    ├── dates.py                 conversão de datas (compatível com o formato da versão web)
    ├── calendar_engine.py       motor de cálculo de datas/duração
    ├── state.py                 modelo de dados, CRUD, cascata de predecessoras, hierarquia
    ├── storage.py                pasta de trabalho, config, importar/exportar JSON
    ├── xlsx_writer.py            exportação Excel (.xlsx) via zipfile da biblioteca padrão
    ├── html_reports.py           os 4 relatórios, como HTML aberto no navegador
    ├── formatting.py             formatação de datas/horas/moeda
    ├── imagens_util.py           codificação de imagens em base64 (data URL)
    └── ui/
        ├── theme.py              tema visual (ttkbootstrap)
        ├── context.py            estado compartilhado entre as páginas
        ├── dialogs.py             área rolável, galeria/lightbox de imagens, campo data+hora
        ├── main_window.py         janela principal, menu, navegação lateral
        ├── tab_resumo.py
        ├── tab_paradas.py         paradas + calendários
        ├── tab_atividades.py      árvore de atividades + diálogo completo
        ├── tab_tabela.py
        ├── tab_gantt.py           desenho customizado em Canvas
        └── tab_relatorios.py
```

## Compatibilidade com a versão web

Os dois sistemas (este e o [`paradas-programadas/`](../paradas-programadas/) em HTML/JS) usam exatamente os mesmos nomes de campo e o mesmo formato de data (ISO 8601 em UTC) no arquivo JSON — incluindo as fotos, guardadas em base64 dentro do próprio arquivo nos dois casos. Isso significa que dá pra:

- Exportar um backup de uma versão e importar na outra sem perder nada.
- Uma pessoa usar a versão web no dia a dia e outra usar a versão desktop, trocando arquivos `.json` entre si.

## Sobre os relatórios em PDF

Esta versão não tenta gerar PDF diretamente (o que exigiria uma biblioteca pesada como `reportlab` ou `weasyprint`). Em vez disso, cada relatório é montado como uma página HTML e aberta no seu navegador padrão — de lá, "Imprimir → Salvar como PDF" gera o arquivo. É o mesmo mecanismo que a versão web já usa, então o resultado (leiaute, cores, tabelas) é idêntico nas duas versões.

## Limitações conhecidas

- Sem Pillow instalado, a pré-visualização de imagens dentro do app fica desabilitada (mas nada é perdido: as fotos continuam anexadas e salvas normalmente).
- O programa foi pensado para uma pessoa/estação de trabalho por vez — não há sincronização em tempo real entre múltiplos usuários acessando a mesma pasta ao mesmo tempo.
- O motor de cálculo de datas usa a mesma simplificação da versão web: a janela produtiva de cada dia do calendário é sempre contada a partir da meia-noite (ver comentário em `app/calendar_engine.py`).
