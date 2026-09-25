@echo off
cd /d "%~dp0.."
echo Verificando dependencias (ttkbootstrap, Pillow)...
python -m pip show ttkbootstrap >nul 2>nul
if errorlevel 1 (
  echo Instalando dependencias pela primeira vez...
  python -m pip install -r requirements.txt
)
echo Iniciando Paradas Programadas...
python main.py
pause
