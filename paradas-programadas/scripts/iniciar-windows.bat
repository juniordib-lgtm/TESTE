@echo off
cd /d "%~dp0.."
echo Iniciando servidor local em http://localhost:8000 ...
echo (isso permite usar o botao "Escolher pasta" para salvar os dados em disco)
echo Feche esta janela para parar o servidor.
where python >nul 2>nul
if %errorlevel%==0 (
  start "" http://localhost:8000/index.html
  python -m http.server 8000
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    start "" http://localhost:8000/index.html
    py -m http.server 8000
  ) else (
    echo Python nao encontrado. Abrindo o arquivo diretamente no navegador...
    echo (o botao "Escolher pasta" pode nao funcionar sem servidor; use Exportar/Importar)
    start "" index.html
  )
)
pause
