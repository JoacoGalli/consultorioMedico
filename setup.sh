#!/bin/bash

# Script de instalación del Sistema de Turnos Médicos
# Uso: ./setup.sh

echo "======================================"
echo "Sistema de Turnos - Consultorio Médico"
echo "======================================"
echo ""

# Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# Activar entorno virtual
echo "🔧 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📥 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cat > .env << EOL
SECRET_KEY=django-insecure-$(openssl rand -base64 32)
DEBUG=True
EOL
    echo "✅ Archivo .env creado"
else
    echo "ℹ️  Archivo .env ya existe"
fi

# Crear directorios necesarios
echo "📁 Creando directorios..."
mkdir -p static/css static/js media templates

# Aplicar migraciones
echo "🗄️  Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

# Cargar datos iniciales
echo "📊 Cargando datos iniciales..."
python manage.py loaddata turnos/fixtures/initial_data.json

# Crear superusuario
echo ""
echo "👤 Creando usuario administrador (Secretaria)..."
echo "Por favor ingresá los datos del usuario administrador:"
python manage.py createsuperuser

echo ""
echo "✅ ¡Instalación completada!"
echo ""
echo "Para iniciar el servidor ejecutá:"
echo "  source venv/bin/activate"
echo "  python manage.py runserver"
echo ""
echo "Luego abrí tu navegador en: http://127.0.0.1:8000/"
echo ""