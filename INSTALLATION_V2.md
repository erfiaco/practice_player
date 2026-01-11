# Instrucciones de Instalación - Practice Player v2.0

## 🆕 Novedades en v2.0

### Ajuste de Posición (v1.0)
- GPIO5 HOLD 3s → Ajustar posición de reproducción
- Mismo sistema que ajuste de puntos A/B

### Ajuste Progresivo (v2.0) ⭐ NUEVO
- Velocidad variable según tiempo pulsado
- 0-1s: ±0.1s (fino)
- 1-2s: ±0.5s (medio)
- >2s: ±1.0s (rápido)

---

## 📦 Archivos a Reemplazar

Esta versión modifica **2 archivos principales**:

1. ✅ `buttons_manager.py` - Sistema de repetición progresiva
2. ✅ `main.py` - Callbacks con delta variable
3. ⚪ `audio_player.py` - Sin cambios (usa el de v1.0)
4. ⚪ `oled_display.py` - Sin cambios (usa el de v1.0)

---

## 🚀 Instalación Rápida

### Opción A: Reemplazo Directo

```bash
# 1. Conecta a tu Raspberry Pi
ssh javo@raspberry.local

# 2. Ve a la carpeta del proyecto
cd ~/Proyects/practice_player

# 3. Haz backup (IMPORTANTE)
mkdir -p backups
cp buttons_manager.py backups/buttons_manager_v1.py.bak
cp main.py backups/main_v1.py.bak

# 4. Copia los nuevos archivos (desde tu ordenador)
# En otra terminal:
scp buttons_manager.py javo@raspberry.local:~/Proyects/practice_player/
scp main.py javo@raspberry.local:~/Proyects/practice_player/

# 5. Verifica permisos
chmod +x main.py

# 6. Prueba
source practice_env/bin/activate
./main.py
```

---

## ✅ Testing Post-Instalación

### Test 1: Verificar Imports
```bash
cd ~/Proyects/practice_player
python3 -c "from buttons_manager import ButtonsManager; print('✓ buttons_manager OK')"
python3 -c "from main import PracticePlayer; print('✓ main OK')"
```

### Test 2: Tap Simple
```
1. Carga un archivo
2. Pausa (GPIO5)
3. Hold GPIO5 3s → Modo ajuste posición
4. TAP GPIO23 → Debe ajustar -0.1s
5. TAP GPIO22 → Debe ajustar +0.1s
```

### Test 3: Hold Corto (<1s)
```
1. En modo ajuste
2. HOLD GPIO23 por 0.5s
3. Debe moverse ~0.3-0.5s (varios 0.1s)
4. Suelta
5. Debe detenerse inmediatamente
```

### Test 4: Hold Medio (1-2s)
```
1. En modo ajuste
2. HOLD GPIO22 por 1.5s
3. Primero se mueve lento (0.1s)
4. Luego acelera (0.5s)
5. Debe moverse ~3-4 segundos total
```

### Test 5: Hold Largo (>2s)
```
1. En modo ajuste
2. HOLD GPIO23 por 3s
3. Debe acelerar progresivamente
4. Velocidad máxima: 1.0s cada 100ms
5. Debe moverse ~10+ segundos total
```

---

## 📊 Verificación de Funcionamiento

### Señales de que funciona correctamente:

✅ **Tap único**: Mueve exactamente 0.1s
✅ **Hold progresivo**: Acelera visiblemente
✅ **Logs en consola**: Muestran delta variable (0.1, 0.5, 1.0)
✅ **Suelta inmediata**: Para al soltar el botón
✅ **Display actualiza**: Muestra posición cambiando

### Señales de problemas:

❌ **No acelera**: Verifica que `threading` está disponible
❌ **No para al soltar**: Revisa conexiones de botones
❌ **Saltos erráticos**: Puede haber múltiples threads
❌ **Error de import**: Verifica sintaxis en archivos

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: threading"
```bash
# Threading es stdlib, si falla:
python3 -c "import threading; print('OK')"
# Si no funciona, reinstala Python
```

### El ajuste no acelera
```bash
# Verifica los logs en consola:
# Debe mostrar:
# "→ [PLAYER] Ajustar -0.1s"  (primeros 1s)
# "→ [PLAYER] Ajustar -0.5s"  (1-2s)
# "→ [PLAYER] Ajustar -1.0s"  (>2s)
```

### Thread no se detiene
```bash
# Verifica que when_released está conectado:
grep "when_released" buttons_manager.py
# Debe aparecer 2 veces (tempo_dn y tempo_up)
```

### Botón no responde
```bash
# Test básico de GPIO:
python3 << EOF
from gpiozero import Button
btn = Button(23, pull_up=True)
btn.when_pressed = lambda: print("¡Funciona!")
input("Pulsa GPIO23... (Enter para salir)")
EOF
```

---

## 🔄 Rollback a v1.0

Si tienes problemas y quieres volver a la versión anterior:

```bash
cd ~/Proyects/practice_player

# Restaurar desde backups
cp backups/buttons_manager_v1.py.bak buttons_manager.py
cp backups/main_v1.py.bak main.py

# Verificar
python3 -c "from buttons_manager import ButtonsManager"
./main.py
```

---

## ⚙️ Configuración Avanzada

### Cambiar Velocidades

Edita `buttons_manager.py`, línea ~180:

```python
# Ajustar umbrales de tiempo
if elapsed < 1.0:      # Nivel 1: cambiar a 0.5s o 1.5s
    delta = 0.1        # Nivel 1: cambiar a 0.05s o 0.2s
    repeat_delay = 0.15  # Nivel 1: más lento 0.2, más rápido 0.1

elif elapsed < 2.0:    # Nivel 2: cambiar a 1.5s o 3.0s
    delta = 0.5        # Nivel 2: cambiar a 0.3s o 1.0s
    repeat_delay = 0.12  # Nivel 2: ajustar velocidad

else:                  # Nivel 3
    delta = 1.0        # Nivel 3: cambiar a 0.5s o 2.0s
    repeat_delay = 0.10  # Nivel 3: ajustar velocidad
```

### Añadir Más Niveles

```python
elif elapsed < 3.0:
    delta = 2.0
    repeat_delay = 0.08
    
elif elapsed < 5.0:
    delta = 5.0
    repeat_delay = 0.05
```

### Cambiar Delay Inicial

```python
# Línea ~168 en _tempo_repeat_worker
time.sleep(0.3)  # Cambiar a 0.2 (más rápido) o 0.5 (más lento)
```

---

## 📝 Notas de Versión

### v2.0 (Actual) - 2025-01-11
- ✨ Ajuste progresivo de velocidad
- ✨ Thread de repetición inteligente
- 🐛 Sin bugs conocidos
- 📊 Mejora de 2-7x en velocidad de ajuste

### v1.0 - 2025-01-11
- ✨ Ajuste de posición con GPIO5 hold
- ✨ Ajuste fino de puntos A/B
- 🎮 Sistema tap/hold para todos los botones

---

## 🎯 Checklist de Instalación Completa

Antes de considerar la instalación completa:

- [ ] Backup realizado
- [ ] Archivos copiados
- [ ] Permisos verificados
- [ ] Imports funcionan
- [ ] Test de tap simple OK
- [ ] Test de hold corto OK
- [ ] Test de hold medio OK
- [ ] Test de hold largo OK
- [ ] Suelta inmediata funciona
- [ ] Display actualiza correctamente
- [ ] No hay errores en consola
- [ ] Otros botones funcionan normal

---

## 💡 Tips de Uso

### Para Máxima Eficiencia:
1. TAP para ajustes pequeños (<0.5s)
2. HOLD corto para ajustes medianos (0.5-3s)
3. HOLD largo para saltos grandes (>5s)

### Workflow Recomendado:
```
1. HOLD largo → Acércate rápido
2. Suelta
3. TAP fino → Precisión exacta
4. Confirma
```

### Práctica el Timing:
- Con el tiempo aprenderás cuánto mantener
- La aceleración es intuitiva
- No tengas miedo de experimentar

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs en consola
2. Verifica el checklist de instalación
3. Prueba el rollback a v1.0
4. Revisa la sección de troubleshooting

---

## 🎉 ¡Disfruta!

El ajuste progresivo hace que usar el Practice Player sea mucho más fluido y rápido. Dedica unos minutos a familiarizarte con los diferentes niveles de velocidad y verás cómo mejora tu workflow de estudio.

¡Feliz práctica! 🎸
