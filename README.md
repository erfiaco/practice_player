# Practice Player

Reproductor para estudiar solos de guitarra con loop A-B y control de tempo.

## Características

- **Navegador de archivos** WAV
- **Loop A-B** con precisión de décimas de segundo
- **Control de tempo** ±1% (50% - 200%)
- **Ajuste fino** de puntos de loop con hold
- **6 botones** para control completo
- **Display OLED** con info en tiempo real

## Instalación

### 1. Dependencias del sistema

```bash
# Librería para time-stretching (Rubber Band)
sudo apt-get update
sudo apt-get install rubberband-cli librubberband-dev

# Crear virtualenv
cd ~/Proyects/practice_player
python3 -m venv practice_env
source practice_env/bin/activate

# Python packages (dentro del virtualenv)
pip install pyrubberband soundfile sounddevice numpy scipy luma.oled pillow gpiozero
```

**O simplemente ejecuta el script de instalación:**
```bash
./install.sh
```

### 2. Estructura de carpetas

```
practice_player/
├── main.py
├── file_browser.py
├── audio_player.py
├── buttons_manager.py
├── oled_display.py
└── audio_files/          ← Coloca aquí tus archivos WAV
    ├── solo_1.wav
    ├── solo_2.wav
    └── ...
```

## Uso

### Modo BROWSER (navegación)

```
GPIO23 → Archivo anterior
GPIO22 → Archivo siguiente
GPIO13 SHORT → Seleccionar archivo (pasar a modo PLAYER)
GPIO13 HOLD (3s) → Salir al boot menu
```

### Modo PLAYER (reproducción)

```
GPIO5  → Play/Pause
GPIO26 TAP → Marcar/desmarcar punto A
GPIO26 HOLD → Ajustar punto A (±0.1s con GPIO23/22)
GPIO6  TAP → Marcar/desmarcar punto B
GPIO6  HOLD → Ajustar punto B (±0.1s con GPIO23/22)
GPIO13 SHORT → Stop
GPIO13 HOLD (3s) → Volver a BROWSER
GPIO23 → Tempo -1% (o ajustar -0.1s en modo hold)
GPIO22 → Tempo +1% (o ajustar +0.1s en modo hold)
```

## Flujo de trabajo típico

1. **Navegar** con GPIO23/22 hasta encontrar el archivo deseado
2. **Seleccionar** con GPIO13 (short press)
3. **Reproducir** con GPIO5
4. **Marcar punto A** cuando empiece el solo (GPIO26 tap)
5. **Marcar punto B** cuando termine el solo (GPIO6 tap)
6. **Ajustar tempo** con GPIO23/22 (ej: 85% para bajar velocidad)
7. **Ajustar fino** los puntos con hold de GPIO26/GPIO6
8. **Practicar** el loop infinitamente

## Display OLED

### Pantalla Browser
```
┌────────────────────────┐
│ BROWSER                │
│ > solo_django.wav      │
│   3/15 files           │
│ SELECT=Load HOLD=Exit  │
└────────────────────────┘
```

### Pantalla Player
```
┌────────────────────────┐
│ ▶ PLAYING [A-B] 85%    │
│ 00:12.3 / 00:45.8      │
│ A:00:08.1 B:00:15.7    │
│ PLAY A B STOP(3s)=Back │
└────────────────────────┘
```

### Pantalla Ajuste Fino
```
┌────────────────────────┐
│   ADJUSTING POINT A    │
│                        │
│    00:08.147           │
│                        │
│  ◀ -0.1s    +0.1s ▶    │
└────────────────────────┘
```

## Integración con Boot Menu

El programa se integra automáticamente con el boot menu. Al salir (GPIO13 hold desde browser), vuelve al menú principal.

## Próximas mejoras (TODO)

- [ ] Implementar time-stretching real con pyrubberband
- [ ] Cache de tempos pre-procesados (80%, 90%, 100%)
- [ ] Soporte para MP3 (conversión automática)
- [ ] Visualización de forma de onda
- [ ] Tap tempo para detectar BPM
- [ ] Exportar sección A-B como nuevo archivo

## Notas técnicas

- **Precisión temporal**: 0.1s (±4-5 frames @ 44.1kHz)
- **Rango de tempo**: 50% - 200% en pasos de 1%
- **Formato soportado**: WAV (mono/estéreo, cualquier sample rate)
- **Latencia**: ~40ms (heredada del looper)

## Troubleshooting

### No hay archivos disponibles
- Verifica que la carpeta `audio_files/` exista
- Asegúrate de que los archivos sean `.wav` (no `.mp3`)
- Usa `file archivo.wav` para verificar el formato

### Audio distorsionado al cambiar tempo
- Verifica que `pyrubberband` esté instalado correctamente
- Prueba con rangos menores (90%-110%)

### Botones no responden
- Revisa conexiones GPIO
- Verifica que no haya conflictos con otros programas
- Comprueba logs con `dmesg | tail`
