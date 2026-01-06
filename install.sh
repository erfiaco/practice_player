#!/bin/bash
# Script de instalación para Practice Player (con virtualenv)

echo "=== Practice Player - Instalación ==="
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Función para verificar éxito
check_success() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 - Error"
        exit 1
    fi
}

echo "1. Actualizando repositorios..."
sudo apt-get update > /dev/null 2>&1
check_success "Repositorios actualizados"

echo ""
echo "2. Instalando Rubber Band Library (sistema)..."
sudo apt-get install -y rubberband-cli librubberband-dev > /dev/null 2>&1
check_success "Rubber Band instalado"

echo ""
echo "3. Creando virtualenv 'practice_env'..."
python3 -m venv practice_env
check_success "Virtualenv creado"

echo ""
echo "4. Instalando dependencias Python en virtualenv..."

# Activar virtualenv y instalar paquetes
source practice_env/bin/activate

# sounddevice
pip install sounddevice > /dev/null 2>&1
check_success "sounddevice instalado"

# soundfile
pip install soundfile > /dev/null 2>&1
check_success "soundfile instalado"

# numpy
pip install numpy > /dev/null 2>&1
check_success "numpy instalado"

# scipy
pip install scipy > /dev/null 2>&1
check_success "scipy instalado"

# luma.oled
pip install luma.oled > /dev/null 2>&1
check_success "luma.oled instalado"

# pillow
pip install pillow > /dev/null 2>&1
check_success "pillow instalado"

# pyrubberband
pip install pyrubberband > /dev/null 2>&1
check_success "pyrubberband instalado"

# gpiozero (si no está ya)
pip install gpiozero > /dev/null 2>&1
check_success "gpiozero instalado"

deactivate

echo ""
echo "5. Creando estructura de carpetas..."
mkdir -p audio_files
check_success "Carpeta audio_files creada"

echo ""
echo "6. Haciendo scripts ejecutables..."
chmod +x main.py test_components.py run.sh
check_success "Scripts ejecutables"

echo ""
echo -e "${GREEN}=== Instalación completada ===${NC}"
echo ""
echo "Próximos pasos:"
echo "1. Coloca tus archivos WAV en: ./audio_files/"
echo "2. Ejecuta:"
echo "   ${YELLOW}./run.sh${NC}  (ejecuta automáticamente con virtualenv)"
echo "   o manualmente:"
echo "   ${YELLOW}source practice_env/bin/activate${NC}"
echo "   ${YELLOW}./main.py${NC}"
echo ""
echo "Para integrar con boot_menu:"
echo "   Ver: ${YELLOW}BOOT_MENU_INTEGRATION.md${NC}"
echo ""
echo "Para probar componentes:"
echo "   ${YELLOW}source practice_env/bin/activate${NC}"
echo "   ${YELLOW}./test_components.py${NC}"
echo ""
