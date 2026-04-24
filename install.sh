#!/bin/bash

# Script de instalación para Book Uploader
# Este script configura todo lo necesario para ejecutar la aplicación

echo "🚀 Book Uploader - Instalación"
echo "=============================="
echo ""

# Verificar Python
echo "✓ Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instálalo primero."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  Python $PYTHON_VERSION encontrado ✓"
echo ""

# Crear entorno virtual
echo "✓ Creando entorno virtual..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Entorno virtual creado ✓"
else
    echo "  Entorno virtual ya existe ✓"
fi
echo ""

# Activar entorno virtual
echo "✓ Activando entorno virtual..."
source venv/bin/activate
echo "  Entorno virtual activado ✓"
echo ""

# Instalar dependencias
echo "✓ Instalando dependencias..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "  Dependencias instaladas ✓"
echo ""

echo "=============================="
echo "✅ ¡Instalación completada!"
echo "=============================="
echo ""
echo "Para ejecutar la aplicación, usa:"
echo "  source venv/bin/activate"
echo "  python main.py"
echo ""
