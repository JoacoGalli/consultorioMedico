#!/bin/sh
set -e

echo "Esperando a la base de datos..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Base de datos lista!"

echo "Ejecutando migrate..."
python manage.py migrate --noinput

echo "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "Iniciando servidor..."
exec "$@"
