#!/usr/bin/env bash
# Script de build para Render / Railway
set -e

echo "==> Instalando dependências..."
pip install -r requirements.txt

echo "==> Coletando arquivos estáticos..."
python manage.py collectstatic --no-input

echo "==> Rodando migrations..."
python manage.py migrate

echo "==> Build concluído!"
