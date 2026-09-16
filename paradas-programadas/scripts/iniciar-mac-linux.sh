#!/bin/bash
# Inicia um servidor local simples e abre o sistema no navegador.
# Rodar via servidor (em vez de abrir o index.html direto) garante que o
# botao "Escolher pasta" funcione em todos os navegadores baseados em Chromium.
cd "$(dirname "$0")/.."
PORT=8000
URL="http://localhost:$PORT/index.html"

abrir_navegador() {
  if command -v open >/dev/null 2>&1; then open "$URL"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"
  fi
}

if command -v python3 >/dev/null 2>&1; then
  echo "Servidor local em $URL (Ctrl+C para parar)"
  ( sleep 1; abrir_navegador ) &
  python3 -m http.server "$PORT"
elif command -v python >/dev/null 2>&1; then
  echo "Servidor local em $URL (Ctrl+C para parar)"
  ( sleep 1; abrir_navegador ) &
  python -m SimpleHTTPServer "$PORT"
else
  echo "Python nao encontrado. Abrindo o arquivo diretamente no navegador."
  echo "(o botao 'Escolher pasta' pode nao funcionar sem servidor; use Exportar/Importar)"
  abrir_navegador
fi
