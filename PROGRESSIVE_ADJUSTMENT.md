# Ajuste Progresivo - Mejora de Velocidad Variable

## 🚀 Nueva Funcionalidad

Ahora los botones de ajuste fino (GPIO23/22) tienen **velocidad progresiva** según cuánto tiempo mantengas pulsado el botón. ¡Es como tener "turbo" incorporado!

## ⚡ Cómo Funciona

Cuando estás en **modo ajuste** (posición, punto A, o punto B):

### Nivel 1: Ajuste Fino (0-1 segundo)
- **Delta**: ±0.1 segundos
- **Velocidad**: Cada 150ms
- **Uso**: Para ajustes precisos, encontrar el punto exacto

### Nivel 2: Ajuste Medio (1-2 segundos)
- **Delta**: ±0.5 segundos  
- **Velocidad**: Cada 120ms (más rápido)
- **Uso**: Para movimientos medianos, recorrer unos segundos

### Nivel 3: Ajuste Rápido (>2 segundos)
- **Delta**: ±1.0 segundo completo
- **Velocidad**: Cada 100ms (muy rápido)
- **Uso**: Para moverse rápidamente por el audio

## 📊 Ejemplo Visual

```
Mantener GPIO23 (atrasar):

Tiempo → 0s ────1s────────2s────────→
Delta  → 0.1    0.5       1.0
         ▼      ▼▼        ▼▼▼
Vel.   → lento  medio     rápido
```

## 🎯 Casos de Uso

### Ejemplo 1: Ajuste de Precisión
```
Situación: Encontrar el inicio exacto de una nota
1. Entra en modo ajuste de posición (GPIO5 hold 3s)
2. TAP GPIO23 varias veces → Ajusta -0.1s cada vez
3. Encuentras el punto exacto rápidamente
```

### Ejemplo 2: Recorrer Rápidamente
```
Situación: Mover el punto A 5 segundos hacia atrás
1. Entra en modo ajuste punto A (GPIO26 hold)
2. MANTÉN GPIO23 por 2+ segundos → Retrocede a -1.0s cada 100ms
3. En ~500ms retrocedes los 5 segundos
4. TAP GPIO22 para ajuste fino si necesitas
```

### Ejemplo 3: Búsqueda Eficiente
```
Situación: Buscar el final de un solo largo
1. Marca punto A al inicio
2. Entra en modo ajuste punto B (GPIO6 hold)
3. MANTÉN GPIO22 → Avanza rápido hasta encontrar el final
4. Suelta y haz taps finos para precisión
```

## 🔧 Detalles Técnicos

### Sistema de Repetición
- **Primera pulsación**: Inmediata con delta=0.1s
- **Delay inicial**: 300ms antes de empezar a repetir
- **Thread dedicado**: Maneja la repetición sin bloquear otros botones

### Transiciones Suaves
```
0.0s → Primera pulsación (0.1s)
0.3s → Empieza repetición (0.1s cada 150ms)
1.0s → Cambia a velocidad media (0.5s cada 120ms)
2.0s → Cambia a velocidad rápida (1.0s cada 100ms)
```

### Matemáticas del Sistema
```python
# Determinar delta según tiempo transcurrido
if tiempo_pulsado < 1.0:
    delta = 0.1s
    repeat_delay = 0.15s
elif tiempo_pulsado < 2.0:
    delta = 0.5s
    repeat_delay = 0.12s
else:
    delta = 1.0s
    repeat_delay = 0.10s
```

## 📝 Cambios en el Código

### buttons_manager.py
- ✅ Añadido `hold_time=0.3` a GPIO23/22
- ✅ Nuevo thread worker `_tempo_repeat_worker`
- ✅ Sistema de callbacks con parámetro `delta`
- ✅ Tracking de tiempo de pulsación

### main.py
- ✅ Callbacks ahora aceptan `delta` como parámetro
- ✅ Uso dinámico de delta en `adjust_fine()`
- ✅ Logs muestran el delta actual (0.1s, 0.5s, 1.0s)

### Sin Cambios
- ❌ `audio_player.py` - Ya acepta delta variable
- ❌ `oled_display.py` - Muestra el valor actualizado automáticamente

## 🎮 Experiencia de Usuario

### Antes (ajuste fijo):
```
TAP, TAP, TAP, TAP, TAP... → 20 taps para 2 segundos
                            → Tedioso y lento
```

### Ahora (ajuste progresivo):
```
HOLD 2 segundos → Recorres 2 segundos en medio segundo
TAP final       → Ajuste fino de 0.1s
                → ¡Rápido y preciso!
```

## 💡 Tips y Trucos

### Tip 1: Ajuste Mixto
Combina hold + tap para máxima eficiencia:
1. HOLD para acercarte rápido
2. TAP para precisión final

### Tip 2: Suelta a Tiempo
No necesitas mantener hasta el final exacto:
- Suelta cuando estés cerca
- Haz taps finales para precisión

### Tip 3: Practica el Timing
Con el tiempo aprenderás:
- < 1s para pequeños ajustes (0.5s total)
- > 2s para grandes saltos (varios segundos)

## ⚙️ Configuración Avanzada

Si quieres cambiar los tiempos o deltas, edita `buttons_manager.py`:

```python
# Línea ~175 en _tempo_repeat_worker
if elapsed < 1.0:          # Cambiar umbral nivel 1
    delta = 0.1            # Cambiar delta nivel 1
    repeat_delay = 0.15    # Cambiar velocidad nivel 1
elif elapsed < 2.0:        # Cambiar umbral nivel 2
    delta = 0.5            # Cambiar delta nivel 2
    repeat_delay = 0.12    # Cambiar velocidad nivel 2
else:
    delta = 1.0            # Cambiar delta nivel 3
    repeat_delay = 0.10    # Cambiar velocidad nivel 3
```

## 🔄 Retrocompatibilidad

✅ **100% Compatible**: 
- Tap simple sigue funcionando igual (0.1s)
- No afecta al ajuste de tempo (sigue siendo ±1%)
- Solo mejora el ajuste fino en modo hold

## 🐛 Troubleshooting

### El ajuste no acelera
- Asegúrate de mantener pulsado > 1 segundo
- Verifica que estás en modo ajuste (ADJUSTING POSITION/POINT A/B)

### Se mueve demasiado rápido
- No mantengas pulsado más de 2 segundos
- Usa taps rápidos en vez de hold

### Quiero más control
- Ajusta los umbrales en `buttons_manager.py`
- Considera añadir más niveles (3s, 4s...)

## 📊 Comparativa de Rendimiento

| Tarea | Antes (0.1s fijo) | Ahora (progresivo) |
|-------|-------------------|-------------------|
| Ajustar 0.5s | 5 taps (1s) | 1 tap o 1s hold |
| Ajustar 2s | 20 taps (4s) | 2s hold (~400ms) |
| Ajustar 10s | 100 taps (20s) | 2s hold (~1s) |

**Mejora**: ⬆️ Hasta **20x más rápido** en ajustes grandes

## 🎸 Workflow Recomendado

### Para estudiar un solo:
```
1. Marca punto A (inicio del solo)
2. Hold GPIO26 → Entra en ajuste A
3. HOLD GPIO23 2+ segundos → Retrocede rápido al verdadero inicio
4. TAP para precisión
5. Confirma con GPIO5

6. Marca punto B (final del solo)  
7. Hold GPIO6 → Entra en ajuste B
8. HOLD GPIO22 2+ segundos → Avanza rápido al verdadero final
9. TAP para precisión
10. Confirma con GPIO5

¡Loop perfecto en segundos!
```

## ⭐ Beneficios Clave

1. **Eficiencia**: Hasta 20x más rápido en ajustes grandes
2. **Precisión**: Mantiene el ajuste fino de 0.1s
3. **Intuitivo**: Se adapta automáticamente a tu necesidad
4. **Sin Cambios**: Todo lo demás funciona igual

¡Disfruta del ajuste turbo! 🚀
