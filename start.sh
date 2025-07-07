#!/usr/bin/env bash
set -euo pipefail

# Mensajes a mostrar
msg="para produccion ejecutar uv remove psycopg y psycopg2"
instruction="al agregar dependencias especificas para el desarrollo especificar arriba"

# Ancho de la terminal
width=$(tput cols)

# Función para centrar y rellenar con '-'
center() {
  local text="$1"
  local len=${#text}
  local pad=$(( width - len ))
  local left=$(( pad / 2 ))
  local right=$(( pad - left ))
  printf '%*s%s%*s\n' "$left" '' "$text" "$right" '' | tr ' ' '-'
}

# Muestra los banners
center "$msg"
center "$instruction"

# Arranca Uvicorn apuntando a la ASGI app dentro de esta carpeta
# Usamos `..` para salir de myweb y que encuentre la misma estructura de módulos
exec uvicorn myweb.asgi:application \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --reload