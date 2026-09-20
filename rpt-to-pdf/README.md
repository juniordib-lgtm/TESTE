# RPT to PDF

Ferramenta de linha de comando que converte relatórios Crystal Reports
(`.rpt`) em PDF.

## Por que isso só roda no Windows

O formato `.rpt` é proprietário da SAP. Não existe biblioteca open-source
(nem multiplataforma) capaz de ler esse formato de forma confiável — a
única forma real de renderizar um `.rpt` é usar o próprio motor da SAP.

Este projeto usa o **SAP Crystal Reports Runtime Engine for .NET
Framework**, o SDK oficial e gratuito de redistribuição da SAP. Ele:

- Só existe para Windows.
- Só é suportado em **.NET Framework** (não funciona em .NET Core/5+/6+/Linux).
- Precisa ser instalado na máquina que for gerar os PDFs (não é um pacote NuGet).

Por isso este código foi escrito, mas **não pôde ser testado neste
ambiente** (um container Linux, sem Windows e sem a licença/runtime da
SAP). Ele foi implementado seguindo a API padrão e documentada do
`CrystalDecisions.CrystalReports.Engine`, mas você deve validar a
compilação e a execução numa máquina Windows antes de usar em produção.

## Pré-requisitos

1. **Windows** (10/11 ou Windows Server).
2. **.NET Framework 4.8 Developer Pack** — https://dotnet.microsoft.com/download/dotnet-framework/net48
3. **SAP Crystal Reports Runtime Engine for .NET Framework** (a versão
   "CRRuntime_64bit" ou "CRRuntime_32bit", conforme seu SO):
   - Baixe em https://help.sap.com/docs/SAP_CRYSTAL_REPORTS_DEVELOPER_VERSION_FOR_VISUAL_STUDIO
     (procure por "Runtime downloads" / "Redistributable").
   - Instale antes de compilar o projeto.
4. Depois de instalado, confira o caminho real das DLLs
   (`CrystalDecisions.CrystalReports.Engine.dll`,
   `CrystalDecisions.Shared.dll`, `CrystalDecisions.ReportAppServer.ClientDoc.dll`)
   e ajuste o `HintPath` em `src/RptToPdf/RptToPdf.csproj` se for diferente
   do caminho padrão já configurado.

## Compilar

```
dotnet build rpt-to-pdf/RptToPdf.sln -c Release
```

(ou abra a `.sln` no Visual Studio e compile por lá — como o SDK do
Crystal Reports depende fortemente da GAC e de registro no Windows,
compilar pelo Visual Studio costuma ser mais tranquilo na primeira vez).

## Usar

Converter um único relatório:

```
rpttopdf --input relatorio.rpt --output relatorio.pdf
```

Se `--output` for omitido, o PDF é salvo ao lado do `.rpt`, com o mesmo
nome.

Passar parâmetros do relatório:

```
rpttopdf --input vendas.rpt --output vendas.pdf ^
  --param DataInicio=2026-01-01 --param DataFim=2026-01-31
```

Informar login de banco de dados (quando o relatório não estiver
configurado para conectar sozinho):

```
rpttopdf --input vendas.rpt --output vendas.pdf ^
  --db-server MEUSERVIDOR --db-name MeuBanco --db-user usuario --db-password ***
```

Converter todos os `.rpt` de uma pasta de uma vez:

```
rpttopdf --input-dir C:\relatorios --output-dir C:\relatorios\pdf
```

Ver todas as opções:

```
rpttopdf --help
```

## Estrutura

```
rpt-to-pdf/
├─ RptToPdf.sln
└─ src/RptToPdf/
   ├─ RptToPdf.csproj      referência ao SDK do Crystal Reports (net48)
   ├─ Program.cs           ponto de entrada / CLI
   ├─ ArgumentosCli.cs     parsing dos argumentos de linha de comando
   └─ ConversorRelatorio.cs  abre o .rpt, aplica parâmetros/login, exporta PDF
```

## Limitações conhecidas

- Só roda em Windows com o runtime da SAP instalado — não há alternativa
  multiplataforma para ler `.rpt` de verdade.
- Relatórios com fonte de dados baseada em servidor exigem que o
  servidor esteja acessível na máquina onde a conversão roda.
- Fórmulas passadas via `--formula` sobrescrevem o texto da fórmula no
  documento em memória; isso não altera o arquivo `.rpt` original.
