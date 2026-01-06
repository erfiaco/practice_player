# Practice Player - Guía Rápida

## Instalación en 5 pasos

### 1. Copiar archivos a la Raspberry Pi
```bash
# Desde tu ordenador
scp -r practice_player/ javo@raspberry.local:~/Proyects/
```

### 2. Ejecutar instalación (crea virtualenv y instala todo)
```bash
ssh javo@raspberry.local
cd ~/Proyects/practice_player
./install.sh
```

### 3. Añadir archivos WAV
```bash
# Copia tus archivos de estudio
cp /path/to/your/solos/*.wav audio_files/
```

### 4. Test rápido
```bash
source practice_env/bin/activate
./test_components.py
```

### 5. Ejecutar
```bash
source practice_env/bin/activate
./main.py
```

**Nota:** El virtualenv se llama `practice_env` (igual que el looper usa `looper_env`).

## Uso Básico

### Seleccionar un archivo
```
1. GPIO23/22 → Navegar
2. GPIO13 SHORT → Seleccionar
```

### Crear loop de práctica
```
1. GPIO5 → Play
2. (Escuchar hasta el inicio del solo)
3. GPIO26 → Marcar punto A
4. (Escuchar hasta el final del solo)
5. GPIO6 → Marcar punto B
6. (El audio ahora hace loop A-B automáticamente)
```

### Ajustar tempo
```
GPIO23 → Más lento (-1%)
GPIO22 → Más rápido (+1%)

Ejemplo: 85% = 15% más lento (ideal para estudiar)
```

### Ajuste fino de puntos
```
1. HOLD GPIO26 → Entrar en modo ajuste A
2. GPIO23/22 → Mover ±0.1s
3. GPIO5 → Confirmar
```

## Integración con Boot Menu

Ver archivo: `BOOT_MENU_INTEGRATION.md`

## Estructura de carpetas

```
practice_player/
├── main.py              ← Programa principal
├── install.sh           ← Script de instalación
├── test_components.py   ← Tests
├── README.md            ← Documentación completa
├── QUICKSTART.md        ← Este archivo
└── audio_files/         ← TUS ARCHIVOS WAV AQUÍ
    ├── solo_1.wav
    └── solo_2.wav
```

## Troubleshooting Rápido

### No hay archivos
```bash
# Verificar
ls audio_files/*.wav

# Convertir MP3 → WAV
ffmpeg -i input.mp3 -ar 44100 -ac 2 output.wav
```

### Botones no responden
```bash
# Verificar GPIO
gpio readall

# Reiniciar programa
# (GPIO13 hold 3s desde browser)
```

### Audio distorsionado
```bash
# Reducir rango de tempo
# Usar 90%-110% en vez de 50%-200%
```

## Próximos pasos

1. Practica con archivos de prueba
2. Ajusta puntos A-B con precisión
3. Encuentra el tempo ideal para cada solo
4. Exporta secciones procesadas (próxima feature)

## Documentación completa

- `README.md` - Todo sobre el programa
- `BOOT_MENU_INTEGRATION.md` - Integrar con boot menu
- `audio_files/README.md` - Gestión de archivos

## Soporte

¿Problemas? Ejecuta:
```bash
./test_components.py
```

¡A practicar! 🎸
