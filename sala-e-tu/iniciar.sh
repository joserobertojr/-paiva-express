#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo ""
echo "  ✈️  SaleTur — Sistema de Viagens"
echo "  Acesse: http://localhost:8000"
echo "  Login: admin / admin123"
echo "  (Ctrl+C para encerrar)"
echo ""
python manage.py runserver
