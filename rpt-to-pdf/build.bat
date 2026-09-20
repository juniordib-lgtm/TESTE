@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  rpttopdf - build automatico
echo ============================================================
echo.

set "TEM_SDK="
for /f "delims=" %%V in ('dotnet --list-sdks 2^>nul') do set "TEM_SDK=1"

if not defined TEM_SDK (
    echo [ERRO] Nenhum .NET SDK encontrado nesta maquina.
    echo.
    echo Se o comando "dotnet" existe mas isso ainda aparece, e porque so o
    echo .NET RUNTIME esta instalado ^(por outro programa^), nao o SDK ^-^-
    echo sao instaladores diferentes.
    echo.
    echo Baixe e instale o ".NET SDK 8.0" ^(nao o "Runtime", nao o
    echo "ASP.NET Core Runtime"^) e rode este build.bat de novo:
    echo   https://dotnet.microsoft.com/download/dotnet/8.0
    echo.
    echo Isso e so uma ferramenta de compilacao, uma unica vez ^-^-
    echo nao precisa ficar instalado na maquina que so vai RODAR o rpttopdf.exe.
    pause
    exit /b 1
)

echo Procurando a instalacao do SAP Crystal Reports Runtime...
set "CAMINHO_CR="
if not "%~1"=="" set "CAMINHO_CR=%~1"

if "%CAMINHO_CR%"=="" (
    for %%D in (
        "C:\Program Files (x86)\SAP BusinessObjects"
        "C:\Program Files\SAP BusinessObjects"
        "C:\Program Files (x86)\Business Objects"
        "C:\Program Files\Business Objects"
    ) do (
        if "!CAMINHO_CR!"=="" if exist "%%~D" (
            for /f "delims=" %%F in ('dir /s /b "%%~D\CrystalDecisions.CrystalReports.Engine.dll" 2^>nul') do (
                if "!CAMINHO_CR!"=="" set "CAMINHO_CR=%%~dpF"
            )
        )
    )
)

if "%CAMINHO_CR%"=="" (
    echo [AVISO] Nao encontrei automaticamente as DLLs do Crystal Reports.
    echo Vou tentar compilar com o caminho padrao configurado no .csproj.
    echo Se falhar, edite "CaminhoRuntimeCR" em src\RptToPdf\RptToPdf.csproj
    echo com o caminho real, ou rode:
    echo   build.bat "C:\caminho\onde\estao\as\dll"
) else (
    echo Encontrado em: %CAMINHO_CR%
)

set "PROJETO=%~dp0src\RptToPdf\RptToPdf.csproj"
set "BINRAIZ=%~dp0src\RptToPdf\bin"

echo.
echo Limpando builds antigos ^(evita copiar um .exe desatualizado^)...
if exist "%BINRAIZ%" rmdir /s /q "%BINRAIZ%"

echo.
echo Compilando ^(Release^)...
if "%CAMINHO_CR%"=="" (
    dotnet build "%PROJETO%" -c Release
) else (
    dotnet build "%PROJETO%" -c Release /p:CaminhoRuntimeCR="%CAMINHO_CR%"
)

if errorlevel 1 (
    echo.
    echo [ERRO] A compilacao falhou. Veja a mensagem acima ^-^- geralmente e
    echo o caminho das DLLs do Crystal Reports que precisa ser ajustado.
    pause
    exit /b 1
)

echo.
echo Procurando o rpttopdf.exe gerado...
set "SAIDA="
for /f "delims=" %%F in ('dir /s /b "%BINRAIZ%\rpttopdf.exe" 2^>nul') do (
    if "!SAIDA!"=="" set "SAIDA=%%~dpF"
)

if "%SAIDA%"=="" (
    echo.
    echo [ERRO] O build terminou sem erro, mas rpttopdf.exe nao foi encontrado
    echo dentro de "%BINRAIZ%".
    echo Isso normalmente significa que o build compilou algo diferente do
    echo esperado. Rode manualmente para ver a saida completa:
    echo   dotnet build "%PROJETO%" -c Release
    echo e procure a linha que comeca com "rpttopdf -^> " para achar onde
    echo o .exe realmente foi parar.
    pause
    exit /b 1
)

echo Encontrado em: %SAIDA%

set "PORTATIL=%~dp0portable"
echo.
echo Montando pasta portatil em: %PORTATIL%
if exist "%PORTATIL%" rmdir /s /q "%PORTATIL%"
mkdir "%PORTATIL%"
xcopy "%SAIDA%*" "%PORTATIL%\" /e /i /y

if not exist "%PORTATIL%\rpttopdf.exe" (
    echo.
    echo [ERRO] A copia falhou: rpttopdf.exe nao esta em "%PORTATIL%".
    echo Copie manualmente os arquivos de "%SAIDA%" para "%PORTATIL%".
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  Pronto! Pasta portatil gerada em:
echo    %PORTATIL%
echo.
echo  Copie essa pasta inteira para qualquer PC Windows que ja
echo  tenha o SAP Crystal Reports Runtime instalado e rode:
echo    rpttopdf.exe --input relatorio.rpt --output relatorio.pdf
echo ============================================================
pause
