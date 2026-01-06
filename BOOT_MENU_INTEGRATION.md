# Integración con Boot Menu

Instrucciones para añadir el Practice Player al boot menu existente.

## 1. Ubicación del Practice Player

Asumiendo que instalaste el Practice Player en:
```
/home/Javo/Proyects/practice_player/
```

## 2. Modificar boot_menu.py

Edita el archivo `/home/Javo/Proyects/boot_menu/boot_menu.py` y añade el Practice Player a la lista de programas.

### Localiza la sección de programas

Busca donde defines la lista de programas disponibles. Debería verse algo así:

```python
programs = [
    {
        'name': 'Looper',
        'path': '/home/Javo/Proyects/looper/main.py',
        'description': 'Loop Station'
    },
    {
        'name': 'Shutdown',
        'action': 'shutdown',
        'description': 'Apagar Raspberry Pi'
    }
]
```

### Añade el Practice Player

Inserta el Practice Player ANTES de Shutdown:

```python
programs = [
    {
        'name': 'Looper',
        'path': '/home/Javo/Proyects/looper/main.py',
        'python': '/home/Javo/Proyects/looper/looper_env/bin/python3',
        'description': 'Loop Station'
    },
    {
        'name': 'Practice Player',  # ← NUEVO
        'path': '/home/Javo/Proyects/practice_player/main.py',
        'python': '/home/Javo/Proyects/practice_player/practice_env/bin/python3',  # ← NUEVO virtualenv
        'description': 'Study Player A-B'
    },
    {
        'name': 'Shutdown',
        'action': 'shutdown',
        'description': 'Apagar Raspberry Pi'
    }
]
```

### Modificar cómo se lanzan los programas

Si tu boot_menu aún no lo hace, asegúrate de que use el python específico de cada virtualenv:

```python
# Busca donde se lanza el programa, debería verse algo así:

# ANTES (si está así, hay que cambiarlo):
subprocess.Popen(["/usr/bin/python3", program['path']])

# DESPUÉS (debe quedar así):
python_path = program.get('python', '/usr/bin/python3')
subprocess.Popen([python_path, program['path']])
```

## 3. Verificar que el script es ejecutable

```bash
cd /home/Javo/Proyects/practice_player
chmod +x main.py
```

## 4. Test manual

Prueba que el programa se lanza correctamente desde el boot menu:

```bash
cd /home/Javo/Proyects/boot_menu
./boot_menu.py
```

Deberías ver:
```
1. Looper
2. Practice Player    ← Nuevo
3. Shutdown
```

## 5. Flujo de navegación esperado

```
Boot Menu
    ↓ (Seleccionar Practice Player)
Practice Player - Browser Mode
    ↓ (GPIO13 short - Seleccionar archivo)
Practice Player - Player Mode
    ↓ (GPIO13 hold 3s - Volver)
Practice Player - Browser Mode
    ↓ (GPIO13 hold 3s - Salir)
Boot Menu
```

## 6. Configuración de auto-start (opcional)

Si quieres que el boot menu se lance automáticamente al arrancar:

### Opción A: Via systemd (recomendado)

Crea `/etc/systemd/system/boot-menu.service`:

```ini
[Unit]
Description=Boot Menu for Javo's Projects
After=multi-user.target

[Service]
Type=simple
User=Javo
WorkingDirectory=/home/Javo/Proyects/boot_menu
ExecStart=/usr/bin/python3 /home/Javo/Proyects/boot_menu/boot_menu.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Habilitar:
```bash
sudo systemctl enable boot-menu.service
sudo systemctl start boot-menu.service
```

### Opción B: Via .bashrc (más simple)

Añade al final de `/home/Javo/.bashrc`:

```bash
# Auto-start boot menu on login
if [ -z "$SSH_CONNECTION" ]; then
    cd /home/Javo/Proyects/boot_menu
    ./boot_menu.py
fi
```

## 7. Troubleshooting

### "Permission denied" al lanzar
```bash
chmod +x /home/Javo/Proyects/practice_player/main.py
```

### "Module not found"
Verifica que todos los archivos .py estén en la misma carpeta:
```bash
cd /home/Javo/Proyects/practice_player
ls -l *.py
```

### No responde a botones
- Asegúrate de que solo un programa use GPIO a la vez
- El boot menu debe liberar GPIO antes de lanzar otro programa
- Revisa que el boot menu use el delay de 1.2s (ver main.py del looper)

### Vuelve al boot menu sin querer
- Verifica el hold_time del GPIO13 (3.0 segundos en buttons_manager.py)
- Puede que estés manteniendo el botón demasiado tiempo

## 8. Display OLED - Mensajes en boot menu

Opcionalmente, puedes hacer que el boot menu muestre el nombre del programa seleccionado en el OLED antes de lanzarlo:

```python
# En boot_menu.py, antes de lanzar el programa:
display.show_message(f"Starting {program_name}...")
time.sleep(1)
subprocess.Popen([...])
```

## 9. Verificación final

Checklist antes de dar por completada la integración:

- [ ] Practice Player aparece en el menú
- [ ] Se puede seleccionar y lanzar
- [ ] Los botones funcionan correctamente en modo Browser
- [ ] Los botones funcionan correctamente en modo Player
- [ ] GPIO13 hold (3s) desde Player vuelve a Browser
- [ ] GPIO13 hold (3s) desde Browser vuelve a Boot Menu
- [ ] No hay conflictos de GPIO entre programas
- [ ] El OLED muestra la información correctamente

## 10. Diagrama completo del sistema

```
┌─────────────────┐
│   BOOT MENU     │ ← Auto-start al arrancar (opcional)
│  1. Looper      │
│  2. Practice    │
│  3. Shutdown    │
└────────┬────────┘
         │
         ├──→ Looper → (Looping original)
         │
         ├──→ Practice Player ┬→ Browser (navegar archivos)
         │                    └→ Player (loop A-B, tempo)
         │
         └──→ Shutdown (apagar Pi)
```
