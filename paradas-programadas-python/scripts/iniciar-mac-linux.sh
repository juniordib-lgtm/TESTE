#!/bin/bash
cd "$(dirname "$0")/.."

PYTHON=python3
command -v $PYTHON >/dev/null 2>&1 || PYTHON=python

echo "Verificando dependências (ttkbootstrap, Pillow)..."
if ! $PYTHON -c "import ttkbootstrap" >/dev/null 2>&1; then
  echo "Instalando dependências pela primeira vez..."
  $PYTHON -m pip install -r requirements.txt
fi

echo "Iniciando Paradas Programadas..."
$PYTHON main.py
