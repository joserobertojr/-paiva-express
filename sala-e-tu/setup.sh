#!/bin/bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser --username admin --email admin@salaetu.com
echo "✅ Setup concluído! Execute: source venv/bin/activate && python manage.py runserver"
