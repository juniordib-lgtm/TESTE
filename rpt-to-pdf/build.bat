@echo off
setlocal enabledelayedexpansion

echo ============================================================
echo  rpttopdf - build automatico
echo ============================================================
echo.

where dotnet >nul 2>nul
if errorlevel 1 (
    echo [ERRO] .NET SDK nao encontrado nesta maquina.
    echo.
    echo Instale o .NET SDK ^(gratuito^) e rode este build.bat de novo:
    echo   https://dotnet.microsoft.com/download/dotnet/8.0
    echo.
    echo Isso e so uma ferramenta de compilacao, uma unica vez ^-^-
    echo nao precisa ficar instalado na maquina que so vai RODAR o rpttopdf.exe.
    pause
    exit /b 1
)

echo Procurando a instalacao do SAP Crystal Reports Runtime...
set "CAMINHO_CR="
for %%D in (
    "C:\Program Files (x86)\SAP BusinessObjects"
    "C:\Program Files\SAP BusinessObjects"
    "C:\Program Files (x86)\Business Objects"
    "C:\Program Files\Business Objects"
) do (
    if exist "%%~D" (
        for /f "delims=" %%F in ('dir /s /b "%%~D\CrystalDecisions.CrystalReports.Engine.dll" 2^>nul') do (
            if "!CAMINHO_CR!"=="" set "CAMINHO_CR=%%~dpF"
        )
    )
)

if "%CAMINHO_CR%"=="" (
    echo [AVISO] Nao encontrei automaticamente as DLLs do Crystal Reports.
    echo Vou tentar compilar com o caminho padrao configurado no .csproj.
    echo Se falhar, edite "CaminhoRuntimeCR" em src\RptToPdf\RptToPdf.csproj
    echo com o caminho real, ou rode:
    echo   build.bat "C:\caminho\onde\estao\as\dll"
    echo.
    if not "%~1"=="" set "CAMINHO_CR=%~1"
) else (
    echo Encontrado em: %CAMINHO_CR%
)

echo.
echo Compilando ^(Release^)...
if "%CAMINHO_CR%"=="" (
    dotnet build "%~dp0src\RptToPdf\RptToPdf.csproj" -c Release
) else (
    dotnet build "%~dp0src\RptToPdf\RptToPdf.csproj" -c Release /p:CaminhoRuntimeCR="%CAMINHO_CR%"
)

if errorlevel 1 (
    echo.
    echo [ERRO] A compilacao falhou. Veja a mensagem acima ^-^- geralmente e
    echo o caminho das DLLs do Crystal Reports que precisa ser ajustado.
    pause
    exit /b 1
)

set "SAIDA=%~dp0src\RptToPdf\bin\Release\net48"
set "PORTATIL=%~dp0portable"

echo.
echo Montando pasta portatil em: %PORTATIL%
if exist "%PORTATIL%" rmdir /s /q "%PORTATIL%"
mkdir "%PORTATIL%"
xcopy "%SAIDA%\*" "%PORTATIL%\" /e /i /y >nul

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
