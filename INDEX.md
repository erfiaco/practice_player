# Practice Player - Índice de Archivos Disponibles

## 📦 Versiones Disponibles

### v2.0 - Ajuste Progresivo (ACTUAL) ⭐
**Fecha**: 2025-01-11

**Características**:
- ✅ Ajuste de posición con GPIO5 hold (v1.0)
- ✅ Ajuste progresivo con velocidad variable (v2.0)
  - 0-1s: ±0.1s (ajuste fino)
  - 1-2s: ±0.5s (ajuste medio)  
  - >2s: ±1.0s (ajuste rápido)

**Mejora**: Hasta 7x más rápido en ajustes grandes

---

## 📂 Archivos por Tipo

### 🐍 Código Python (v2.0)

#### buttons_manager.py
- **Qué hace**: Gestión de todos los botones GPIO
- **Cambios v2.0**: 
  - Sistema de repetición progresiva
  - Thread worker para ajuste continuo
  - Detección de tiempo de pulsación
- **Tamaño**: ~10 KB
- **Líneas**: ~280

#### main.py
- **Qué hace**: Programa principal y state machine
- **Cambios v2.0**:
  - Callbacks aceptan delta variable
  - Uso dinámico de delta en ajustes
- **Tamaño**: ~10 KB
- **Líneas**: ~310

#### audio_player.py (sin cambios en v2.0)
- **Qué hace**: Engine de reproducción y loop A-B
- **Incluido en**: Versión v1.0
- **Nota**: Usar la versión de v1.0

#### oled_display.py (sin cambios en v2.0)
- **Qué hace**: Interfaz OLED con layouts
- **Incluido en**: Versión v1.0
- **Nota**: Usar la versión de v1.0

---

### 📚 Documentación

#### PROGRESSIVE_ADJUSTMENT.md
- **Para**: Usuarios finales
- **Contenido**:
  - Explicación de la funcionalidad
  - Casos de uso con ejemplos
  - Tips y trucos
  - Comparativa de rendimiento
  - Workflow recomendado
- **Tamaño**: ~6 KB

#### TECHNICAL_SUMMARY_V2.md
- **Para**: Desarrolladores
- **Contenido**:
  - Cambios línea por línea
  - Flujo de datos completo
  - Tabla de tiempos y velocidades
  - Parámetros ajustables
  - Plan de testing
  - Métricas de código
- **Tamaño**: ~9 KB

#### INSTALLATION_V2.md
- **Para**: Instaladores
- **Contenido**:
  - Pasos de instalación detallados
  - Tests post-instalación
  - Troubleshooting completo
  - Plan de rollback
  - Configuración avanzada
  - Checklist de validación
- **Tamaño**: ~7 KB

---

## 🗂️ Archivos de v1.0 (Incluidos en paquete anterior)

Estos archivos NO han cambiado en v2.0, usar los de v1.0:

- ✅ audio_player.py
- ✅ oled_display.py
- ✅ file_browser.py
- ✅ tempo_controller.py
- ✅ test_components.py
- ✅ README.md
- ✅ QUICKSTART.md

---

## 🎯 Instalación: Qué Archivos Usar

### Para v2.0 Completo:

**Archivos nuevos/actualizados (de este paquete v2.0)**:
```
buttons_manager.py  ← Reemplazar
main.py            ← Reemplazar
```

**Archivos sin cambios (de paquete v1.0)**:
```
audio_player.py
oled_display.py
file_browser.py
tempo_controller.py
test_components.py
```

**Archivos de soporte**:
```
install.sh
run.sh
README.md
QUICKSTART.md
```

---

## 📋 Matriz de Compatibilidad

| Archivo | v1.0 | v2.0 | Compatible |
|---------|------|------|-----------|
| buttons_manager.py | ✅ | ⭐ | ❌ NO (actualizar) |
| main.py | ✅ | ⭐ | ❌ NO (actualizar) |
| audio_player.py | ✅ | - | ✅ SÍ (mantener v1.0) |
| oled_display.py | ✅ | - | ✅ SÍ (mantener v1.0) |
| file_browser.py | ✅ | - | ✅ SÍ (mantener v1.0) |
| tempo_controller.py | ✅ | - | ✅ SÍ (mantener v1.0) |

---

## 🚀 Guía Rápida de Instalación

### Para actualizar de v1.0 a v2.0:

```bash
# 1. Backup
cd ~/Proyects/practice_player
cp buttons_manager.py backups/buttons_manager_v1.py.bak
cp main.py backups/main_v1.py.bak

# 2. Copiar solo 2 archivos nuevos
scp buttons_manager.py main.py javo@raspberry.local:~/Proyects/practice_player/

# 3. Listo! (mantener todo lo demás de v1.0)
./main.py
```

### Para instalación limpia:

```bash
# Necesitas TODOS estos archivos:
# De v2.0:
- buttons_manager.py
- main.py

# De v1.0:
- audio_player.py
- oled_display.py
- file_browser.py
- tempo_controller.py
- test_components.py
- install.sh
- run.sh
```

---

## 📊 Resumen de Mejoras por Versión

### v1.0 → v2.0

**Funcionalidad añadida**:
- Ajuste progresivo de velocidad

**Archivos modificados**:
- buttons_manager.py (+80 líneas)
- main.py (+10 líneas modificadas)

**Mejora de rendimiento**:
- 2-7x más rápido en ajustes
- Hasta 20x en casos extremos

**Compatibilidad**:
- ✅ Retrocompatible (tap sigue igual)
- ✅ Sin nuevas dependencias
- ✅ Sin cambios en hardware

---

## 🎓 Para Cada Perfil de Usuario

### Usuario Final
**Lee**: PROGRESSIVE_ADJUSTMENT.md  
**Enfoque**: Cómo usar la nueva funcionalidad

### Técnico/Instalador  
**Lee**: INSTALLATION_V2.md  
**Enfoque**: Cómo instalar y verificar

### Desarrollador
**Lee**: TECHNICAL_SUMMARY_V2.md  
**Enfoque**: Cómo funciona internamente

---

## 📞 Soporte

Si tienes dudas sobre qué archivos usar:

1. **¿Primera instalación?** → Necesitas v1.0 completo + archivos v2.0
2. **¿Ya tienes v1.0?** → Solo actualiza 2 archivos (buttons_manager, main)
3. **¿Problemas?** → Revisa INSTALLATION_V2.md → Troubleshooting

---

## ✨ Próximos Pasos

1. Lee INSTALLATION_V2.md
2. Haz backup de archivos actuales
3. Copia buttons_manager.py y main.py
4. Prueba con los tests del manual
5. ¡Disfruta del ajuste turbo! 🚀

---

**Versión del Paquete**: v2.0  
**Fecha de Release**: 2025-01-11  
**Archivos incluidos**: 5 (2 código Python + 3 documentación)  
**Compatibilidad**: Requiere v1.0 base
