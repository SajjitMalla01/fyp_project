@echo off
echo Applying recent database schema updates (Removed payment plans)...
cd /d "%~dp0"
python manage.py makemigrations tenants
python manage.py migrate
echo Starting CEMS Django Server...
python manage.py runserver 8000
pause
