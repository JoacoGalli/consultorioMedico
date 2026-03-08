#!/bin/bash

# Script para ejecutar tests del proyecto

echo "======================================"
echo "Ejecutando Tests - Sistema de Turnos"
echo "======================================"
echo ""

# Activar entorno virtual si existe
if [ -d "venv" ]; then
    echo "Activando entorno virtual..."
    source venv/bin/activate
fi

# Limpiar archivos de caché
echo "Limpiando caché..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null

echo ""
echo "Ejecutando tests..."
echo "======================================"

# Ejecutar tests con configuración específica
python manage.py test turnos --settings=consultorio.test_settings --verbosity=2

TEST_EXIT_CODE=$?

echo ""
echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ TODOS LOS TESTS PASARON"
else
    echo "❌ ALGUNOS TESTS FALLARON"
fi
echo "======================================"

exit $TEST_EXIT_CODE