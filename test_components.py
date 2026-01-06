#!/usr/bin/env python3
"""
Script de testing para verificar componentes del Practice Player
"""

import sys
import os

def test_imports():
    """Test 1: Verificar que todos los módulos se pueden importar"""
    print("=== Test 1: Imports ===")
    
    try:
        from file_browser import FileBrowser
        print("✓ FileBrowser importado")
    except Exception as e:
        print(f"✗ FileBrowser: {e}")
        return False
    
    try:
        from audio_player import AudioPlayer
        print("✓ AudioPlayer importado")
    except Exception as e:
        print(f"✗ AudioPlayer: {e}")
        return False
    
    try:
        from tempo_controller import TempoController
        print("✓ TempoController importado")
    except Exception as e:
        print(f"✗ TempoController: {e}")
        return False
    
    try:
        from buttons_manager import ButtonsManager
        print("✓ ButtonsManager importado")
    except Exception as e:
        print(f"✗ ButtonsManager: {e}")
        # No es crítico si no hay GPIO
        print("  (Normal si no estás en la Raspberry Pi)")
    
    try:
        from oled_display import OledDisplay
        print("✓ OledDisplay importado")
    except Exception as e:
        print(f"✗ OledDisplay: {e}")
        # No es crítico si no hay I2C
        print("  (Normal si no estás en la Raspberry Pi)")
    
    return True

def test_file_browser():
    """Test 2: File Browser"""
    print("\n=== Test 2: File Browser ===")
    
    try:
        from file_browser import FileBrowser
        
        browser = FileBrowser(audio_dir="audio_files")
        print(f"✓ Browser creado")
        print(f"  Archivos encontrados: {browser.get_file_count()}")
        
        if browser.has_files():
            print(f"  Archivo actual: {browser.get_current_filename()}")
            print(f"  Posición: {browser.get_position()}")
        else:
            print("  ⚠ No hay archivos WAV en audio_files/")
            print("    Añade archivos .wav para probar completamente")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en File Browser: {e}")
        return False

def test_audio_player():
    """Test 3: Audio Player (sin reproducir)"""
    print("\n=== Test 3: Audio Player ===")
    
    try:
        from audio_player import AudioPlayer
        
        player = AudioPlayer()
        print("✓ Player creado")
        
        # Test de funciones básicas
        player.set_point_a()
        player.clear_point_a()
        print("✓ Funciones de punto A")
        
        player.set_point_b()
        player.clear_point_b()
        print("✓ Funciones de punto B")
        
        player.change_tempo(10)
        print(f"✓ Cambio de tempo: {player.tempo_percent}%")
        
        player.change_tempo(-10)
        print(f"✓ Cambio de tempo: {player.tempo_percent}%")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en Audio Player: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tempo_controller():
    """Test 4: Tempo Controller"""
    print("\n=== Test 4: Tempo Controller ===")
    
    try:
        from tempo_controller import TempoController, RUBBERBAND_AVAILABLE
        import numpy as np
        
        print(f"  Rubber Band disponible: {RUBBERBAND_AVAILABLE}")
        
        controller = TempoController()
        print("✓ Controller creado")
        
        # Audio de prueba
        samplerate = 44100
        duration = 0.5
        audio = np.random.randn(int(samplerate * duration)).astype(np.float32)
        
        # Test cambio de tempo
        processed = controller.change_tempo(audio, samplerate, 90)
        
        if RUBBERBAND_AVAILABLE:
            print(f"✓ Tempo procesado: {len(audio)} → {len(processed)} samples")
            print(f"  Original: {len(audio)/samplerate:.2f}s")
            print(f"  Procesado: {len(processed)/samplerate:.2f}s")
        else:
            print("  ⚠ Rubber Band no disponible, tempo change deshabilitado")
        
        return True
        
    except Exception as e:
        print(f"✗ Error en Tempo Controller: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dependencies():
    """Test 0: Verificar dependencias externas"""
    print("=== Test 0: Dependencias ===")
    
    deps = {
        'sounddevice': 'pip3 install sounddevice',
        'soundfile': 'pip3 install soundfile',
        'numpy': 'pip3 install numpy',
        'scipy': 'pip3 install scipy',
        'PIL': 'pip3 install pillow',
        'pyrubberband': 'pip3 install pyrubberband (requiere rubberband-cli)',
    }
    
    all_ok = True
    for dep, install_cmd in deps.items():
        try:
            __import__(dep)
            print(f"✓ {dep}")
        except ImportError:
            print(f"✗ {dep} - Instalar con: {install_cmd}")
            all_ok = False
    
    return all_ok

def run_all_tests():
    """Ejecuta todos los tests"""
    print("╔════════════════════════════════════════╗")
    print("║  Practice Player - Component Tests    ║")
    print("╚════════════════════════════════════════╝")
    print()
    
    results = []
    
    results.append(("Dependencias", test_dependencies()))
    results.append(("Imports", test_imports()))
    results.append(("File Browser", test_file_browser()))
    results.append(("Audio Player", test_audio_player()))
    results.append(("Tempo Controller", test_tempo_controller()))
    
    # Resumen
    print("\n" + "="*40)
    print("RESUMEN")
    print("="*40)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("="*40)
    print(f"Total: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n✓ Todos los tests OK - Listo para usar")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) fallaron - Revisar instalación")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
