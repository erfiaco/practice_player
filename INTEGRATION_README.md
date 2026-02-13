# Integración de Tempo Control con soundstretch

## Resumen de cambios

Hemos reemplazado `pyrubberband` (demasiado pesado) con `soundstretch` (SoundTouch Library) para el control de tempo. El procesamiento ya NO es en tiempo real, sino que se hace de forma asíncrona cuando el usuario cambia el tempo con reproducción detenida.

---

## 1. Instalación de soundstretch

```bash
sudo apt-get update
sudo apt-get install soundstretch
```

Verificar instalación:
```bash
soundstretch --help
```

---

## 2. Ejecutar tests

Una vez instalado soundstretch, ejecuta el script de test:

```bash
cd /home/claude
./test_soundstretch.py
```

Debería mostrar:
```
✓ PASS     | Instalación
✓ PASS     | Procesamiento básico  
✓ PASS     | TempoController
```

---

## 3. Integrar en tu proyecto

### Opción A: Reemplazar archivos (recomendado)

```bash
# Desde tu carpeta del practice_player
cd ~/Projects/practice_player  # o donde esté tu proyecto

# Backup de archivos actuales
cp tempo_controller.py tempo_controller.py.backup
cp audio_player.py audio_player.py.backup

# Copiar nuevos archivos
cp /home/claude/tempo_controller_soundstretch.py tempo_controller.py
cp /home/claude/audio_player_with_tempo.py audio_player.py
```

### Opción B: Revisar diferencias primero

```bash
# Ver qué cambió
diff tempo_controller.py /home/claude/tempo_controller_soundstretch.py
diff audio_player.py /home/claude/audio_player_with_tempo.py
```

---

## 4. Cambios principales

### `tempo_controller.py`
- ✅ Usa `soundstretch` (subprocess) en lugar de `pyrubberband`
- ✅ Maneja archivos temporales automáticamente
- ✅ Soporte para callback de progreso: `on_progress(mensaje)`
- ✅ Cache de hasta 10 tempos diferentes
- ✅ Opción `-quick` para tempos extremos (>±20%)

### `audio_player.py`
- ✅ `change_tempo()` ahora es asíncrono (usa threads)
- ✅ **Auto-pause** cuando se cambia el tempo
- ✅ Callback de progreso para actualizar el OLED
- ✅ Nuevo estado: `'PROCESSING'` (mientras procesa tempo)
- ✅ Manejo inteligente de loop A-B con tempo modificado
- ✅ Nuevo método: `is_tempo_available()` para verificar si soundstretch está presente

---

## 5. Flujo de uso esperado

### Usuario normal:
1. Cargar archivo WAV
2. Marcar puntos A y B (opcional)
3. **DETENER reproducción** (si estaba reproduciéndose)
4. Cambiar tempo con GPIO23/22 (±1%)
   - Display muestra: "Processing 85%..."
   - Espera 2-5 segundos dependiendo del archivo
   - Display muestra: "✓ Ready at 85%"
5. Presionar PLAY
6. Reproduce a nuevo tempo

### Cambios sucesivos de tempo:
- Si el tempo ya fue procesado antes → **instantáneo** (usa cache)
- Si es un tempo nuevo → procesa de nuevo

### Volver a tempo normal (100%):
- Cambiar a 100% → **instantáneo** (usa audio original sin procesar)

---

## 6. Mensajes de progreso en OLED

El `audio_player` envía estos mensajes al display vía `on_state_change()`:

| Mensaje | Cuándo |
|---------|--------|
| `"Processing 85%..."` | Iniciando procesamiento |
| `"✓ Ready at 85%"` | Procesamiento completado |
| `"✓ Usando cache (85%)"` | Reutilizando tempo previamente procesado |
| `"✗ Error: ..."` | Falló el procesamiento |
| `"✗ Timeout"` | Archivo muy largo (>30s de procesamiento) |

Tu código de `oled_display.py` debe manejar estos mensajes y mostrarlos al usuario.

---

## 7. Comportamiento del cache

### Límite: 10 tempos
- Si procesas 11 tempos diferentes, el más antiguo se borra (FIFO)
- Tempos más usados: 80%, 85%, 90%, 95%, 100%, 105%, 110%, 120%

### Liberación de memoria
Al cargar un nuevo archivo, el cache se limpia automáticamente:
```python
self.tempo_controller.clear_cache()
```

---

## 8. Tiempos de procesamiento esperados

En Raspberry Pi 4:

| Duración del audio | Tempo | Tiempo procesamiento |
|-------------------|-------|---------------------|
| 30 segundos | 85% | ~2 segundos |
| 1 minuto | 90% | ~3 segundos |
| 3 minutos | 80% | ~6-8 segundos |
| 5 minutos | 120% | ~10-12 segundos |

**Nota:** Los tempos extremos (<70% o >130%) pueden tomar más tiempo y usar la opción `-quick`.

---

## 9. Troubleshooting

### "soundstretch no disponible"
```bash
# Verificar instalación
which soundstretch

# Si no existe
sudo apt-get install soundstretch
```

### Procesamiento muy lento
- ¿Archivo muy largo? (>5 min)
- Usa solo loop A-B para procesar menos audio
- soundstretch procesará solo la sección entre A y B

### Audio procesado suena mal
- Tempos muy extremos (<60% o >140%) degradan calidad
- Limitar rango recomendado: 70%-130%

### Cache lleno
```python
# Limpiar manualmente si es necesario
player.tempo_controller.clear_cache()
```

---

## 10. Próximos pasos

### Test manual:
1. Cargar un archivo WAV corto (~30s)
2. Cambiar a 85%
3. Verificar que el display muestra "Processing..."
4. Esperar mensaje "✓ Ready at 85%"
5. Reproducir y verificar que suena más lento
6. Cambiar a 120%
7. Verificar que suena más rápido

### Integración con botones:
- Asegurarte de que los callbacks de GPIO23/22 llamen a `player.change_tempo(±1)`
- El display debe actualizarse con los mensajes de progreso

---

## 11. Comparación pyrubberband vs soundstretch

| Característica | pyrubberband | soundstretch |
|---------------|--------------|--------------|
| Velocidad | ⚠️ Lento (8-15s) | ✅ Rápido (2-5s) |
| Calidad | 🏆 Excelente | ✅ Muy buena |
| Memoria | ⚠️ Alta | ✅ Baja |
| Integración | Python nativo | Subprocess |
| Estabilidad Pi | ❌ Cuelga | ✅ Estable |

---

## Archivos incluidos

```
/home/claude/
├── tempo_controller_soundstretch.py  → reemplaza tempo_controller.py
├── audio_player_with_tempo.py        → reemplaza audio_player.py
└── test_soundstretch.py              → script de prueba
```

---

¿Preguntas? Revisa el código de `audio_player_with_tempo.py` - está bien comentado con los cambios marcados con ⭐.
