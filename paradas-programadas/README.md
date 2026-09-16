# Paradas Programadas

Sistema web local (sem instalação, sem servidor obrigatório, sem internet) para planejar e acompanhar paradas programadas de manutenção.

Tudo roda direto no navegador. Não há backend, não há envio de dados para lugar nenhum.

## Como abrir

**Opção mais simples:** dê duplo clique em `index.html`. Funciona no Chrome, Edge, Firefox e Safari. Os dados ficam salvos automaticamente no navegador (IndexedDB) e continuam lá mesmo se você fechar e abrir de novo.

**Opção com pasta própria no disco:** para usar o botão **"📁 Pasta"** do topo (que salva um arquivo `dados-paradas.json` na pasta que você escolher, além do IndexedDB), abra o sistema através de um servidor local — isso evita restrições de segurança que alguns navegadores aplicam a arquivos abertos direto do disco.

Depois de escolher a pasta uma vez, o sistema lembra dela. Nas próximas vezes, basta clicar em **"📁 Pasta"** para reconectar (não abre um seletor novo). Só é aberto um seletor de pasta quando você clica em **"🔁 Trocar pasta"**, que aparece ao lado assim que uma pasta já foi escolhida — é a forma explícita de apontar para outro lugar.

- **Windows:** dê duplo clique em `scripts/iniciar-windows.bat`.
- **Mac/Linux:** rode `scripts/iniciar-mac-linux.sh` (ou dê duplo clique se seu sistema permitir).

Os dois scripts sobem um servidor local (via Python, que já vem instalado na maioria dos sistemas) e abrem o sistema em `http://localhost:8000`. Nenhum dado sai da sua máquina — o servidor só serve os arquivos do próprio sistema.

Se preferir, qualquer outro servidor estático local funciona (ex.: extensão "Live Server" do VS Code).

> Mesmo sem escolher uma pasta, nada é perdido: os dados sempre ficam salvos no navegador. Use os botões **⬇ Exportar** / **⬆ Importar** a qualquer momento para gerar ou carregar um backup em `.json`.

## O que o sistema tem

1. **Cadastro de Paradas** — nome, local, descrição, status e o calendário utilizado.
2. **Calendários** — perfis reutilizáveis que definem quantas horas por dia contam como "tempo produtivo" da parada, quais dias da semana são úteis e exceções (feriados, dias com capacidade reduzida). É esse calendário que alimenta o cálculo automático de datas.
3. **Atividades e sub-atividades** — cada atividade pode ter uma ou mais sub-atividades, descrição, responsável, área e imagens anexadas (fotos do local, desenhos, etc.). A listagem fica sempre ordenada por Data/Hora de Início, com cada sub-atividade agrupada logo abaixo da atividade correspondente.
4. **Recursos por atividade** — mão de obra, equipamento, material ou serviço, com quantidade, unidade e custo unitário (o sistema soma o custo estimado automaticamente).
5. **Data e duração com cálculo automático** — informe a Data/Hora de Início e a Duração (em horas) que a Data/Hora Fim planejada é calculada sozinha (respeitando o calendário da parada); também funciona ao contrário. Além disso, cada atividade tem campos de **Início real** e **Fim real**, preenchidos conforme o trabalho de fato acontece, com a duração real calculada automaticamente — para comparar planejado × real.
6. **Visão em Tabela e Gantt** — tabela com filtros, ordenação por coluna e exportação para Excel; Gantt com zoom por dia ou semana, barra de progresso, cores por status e uma barra tracejada mostrando a execução real ao lado da planejada.
7. **Resumo** — painel com total de atividades, progresso médio, duração total da parada, recursos por tipo e custo estimado.
8. **Relatórios simplificado e completo/detalhado** — o simplificado é uma tabela enxuta (com datas planejadas e reais); o completo traz descrição, recursos e imagens de cada atividade e sub-atividade.
9. **Relatório Gantt** — o gráfico de Gantt em formato pronto para impressão.
10. **Relatório com Imagens** — galeria de fotos por atividade/sub-atividade, pronta para impressão.
11. **Exportar para Excel** — na aba Tabela, o botão "📊 Exportar Excel" gera um `.xlsx` com duas planilhas (Atividades e Recursos), respeitando os filtros aplicados.
12. **Pré-visualização de imagens** — na aba Atividades, cada atividade com fotos tem um botão "🖼 Ver imagens" que abre uma galeria em tela cheia (com navegação entre fotos); dentro do formulário, clicar em qualquer miniatura também abre essa pré-visualização.

Todos os relatórios têm um botão **"🖨 Imprimir / Salvar PDF"** — use a opção "Salvar como PDF" da caixa de impressão do navegador para gerar o arquivo.

## Sobre o cálculo de datas

O calendário de cada parada define, por dia, quantas horas contam como produtivas (por padrão, 24h/dia — parada rodando contínua). A partir da Data/Hora de Início de uma atividade, o sistema soma as horas de duração informadas pulando automaticamente os trechos de dias não produtivos (dias fora da lista de "dias úteis" do calendário ou marcados como exceção com 0h). Dias com capacidade reduzida (ex.: um feriado com equipe menor, 8h em vez de 24h) contam apenas as horas configuradas para aquele dia — o restante do dia fica de fora do cálculo.

Isso é uma simplificação intencional (a janela produtiva de cada dia é sempre contada a partir da meia-noite), suficiente para o planejamento típico de uma parada, mas não substitui uma ferramenta de cronograma com turnos detalhados por hora do dia.

## Estrutura dos arquivos

```
paradas-programadas/
├── index.html                  ponto de entrada
├── css/style.css
├── js/
│   ├── utils.js                helpers, modal genérico
│   ├── calendar.js             motor de cálculo de datas/duração
│   ├── storage.js               IndexedDB + pasta no disco + exportar/importar
│   ├── state.js                 modelo de dados e CRUD em memória
│   ├── xlsx-writer.js           gerador de planilhas .xlsx sem dependências externas
│   ├── ui-imagens.js            galeria/lightbox de pré-visualização de imagens
│   ├── ui-paradas-calendarios.js
│   ├── ui-atividades.js
│   ├── ui-tabela.js
│   ├── ui-gantt.js
│   ├── ui-resumo.js
│   ├── ui-relatorios.js
│   └── main.js                  navegação entre abas e inicialização
├── scripts/
│   ├── iniciar-windows.bat
│   └── iniciar-mac-linux.sh
└── README.md
```

## Backup e migração entre computadores

Use **⬇ Exportar** para gerar um `.json` com tudo (paradas, calendários, atividades, recursos e imagens embutidas). Em outro computador, abra o sistema e use **⬆ Importar** para carregar esse arquivo — atenção: importar substitui todos os dados atuais daquele navegador.

## Limitações conhecidas

- As imagens ficam guardadas dentro do próprio arquivo de dados (em base64), o que mantém tudo em um único arquivo portátil, mas deixa o `dados-paradas.json` maior conforme mais fotos forem anexadas.
- O botão "Escolher pasta" depende da File System Access API, disponível em navegadores baseados em Chromium (Chrome, Edge, Brave, Opera). Em outros navegadores (Firefox, Safari) os dados continuam salvos automaticamente no navegador; use Exportar/Importar para manter uma cópia em arquivo.
- O sistema foi pensado para uma pessoa/estação de trabalho por vez — não há sincronização em tempo real entre múltiplos usuários.
