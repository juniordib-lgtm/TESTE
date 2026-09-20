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

Na máquina que vai **compilar** (uma vez só):

1. **Windows** (10/11 ou Windows Server) com o **SAP Crystal Reports
   Runtime Engine for .NET Framework** já instalado (é o que você usa
   para abrir/gerar relatórios .rpt normalmente).
2. **.NET SDK** (gratuito) — https://dotnet.microsoft.com/download/dotnet/8.0
   — usado só para compilar; não precisa continuar instalado na máquina
   que vai apenas *rodar* o programa depois.

Na máquina que vai só **rodar** o `rpttopdf.exe` depois de compilado:

- Windows + o mesmo SAP Crystal Reports Runtime Engine instalado.
  (Não existe forma de ler um `.rpt` de verdade sem esse motor presente
  — nenhum programa portátil consegue embutir o motor da SAP dentro de
  um único .exe, porque ele é registrado como componente COM no Windows.)

## Compilar (opção rápida — recomendada)

Dê duplo-clique em `build.bat` (ou rode pelo terminal). Ele:

1. Confere se o `.NET SDK` está instalado.
2. Procura sozinho a pasta onde o Crystal Reports Runtime instalou as
   DLLs (`CrystalDecisions.*.dll`).
3. Compila o projeto.
4. Copia o resultado para uma pasta `portable/` na raiz do repositório —
   é só essa pasta (exe + DLLs, sem instalador) que você copia para
   qualquer outro PC que já tenha o runtime da SAP.

Se ele não achar as DLLs sozinho, rode `build.bat "C:\caminho\onde\estao\as\dll"`
apontando para a pasta certa, ou edite a propriedade `CaminhoRuntimeCR`
em `src/RptToPdf/RptToPdf.csproj`.

O script agora **procura o `rpttopdf.exe` gerado** em vez de assumir um
caminho fixo, e só declara sucesso depois de confirmar que o `.exe` está
de fato dentro de `portable/`. Se algo der errado, ele imprime o motivo
em vez de terminar com uma pasta vazia.

## Compilar (opção manual)

```
dotnet build rpt-to-pdf/RptToPdf.sln -c Release
```

(ou abra a `.sln` no Visual Studio e compile por lá).

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
