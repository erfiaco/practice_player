#!/bin/bash
# Script para ejecutar Practice Player con virtualenv activado

cd "$(dirname "$0")"

if [ ! -d "practice_env" ]; then
    echo "❌ Error: virtualenv 'practice_env' no encontrado"
    echo "Ejecuta primero: ./install.sh"
    exit 1
fi

echo "Activando virtualenv y ejecutando Practice Player..."
source practice_env/bin/activate
./main.py
