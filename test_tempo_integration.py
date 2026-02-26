#!/usr/bin/env python3
import numpy as np
import soundfile as sf
from audio_player import AudioPlayer

# Crear audio de prueba corto
print("Generando audio de prueba...")
samplerate = 44100
duration = 2.0  # 2 segundos
freq = 440
t = np.linspace(0, duration, int(samplerate * duration))
audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
sf.write("/tmp/test_tempo.wav", audio, samplerate)
print("✓ Audio creado: /tmp/test_tempo.wav")

# Callback para ver mensajes
def mostrar_estado(msg):
    print(f"  Estado: {msg}")

# Crear player
player = AudioPlayer(on_state_change=mostrar_estado)

# Test 1: Cargar archivo
print("\n1. Cargando archivo...")
player.load_file("/tmp/test_tempo.wav")

# Test 2: Cambiar tempo (solo número)
print("\n2. Cambiando tempo a 85%...")
player.change_tempo(-15)  # 100 - 15 = 85%
print(f"   Tempo actual: {player.tempo_percent}%")

# Test 3: Presionar play (debería procesar)
print("\n3. Iniciando reproducción (debería procesar primero)...")
player.play()

# Esperar a que termine
import time
time.sleep(5)

player.stop()

print("\n✓ Test completado")
print(f"Cache: {player.tempo_controller.get_cache_info()}")
