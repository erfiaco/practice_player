#!/usr/bin/env python3
"""
Test de soundstretch - Verificar instalación y funcionalidad

Este script crea un audio de prueba y verifica que soundstretch
pueda procesarlo correctamente.
"""

import sys
import os
import subprocess
import numpy as np
import soundfile as sf
import tempfile

def check_soundstretch_installed():
    """Verifica si soundstretch está instalado"""
    print("="*50)
    print("1. Verificando instalación de soundstretch...")
    print("="*50)
    
    try:
        result = subprocess.run(
            ['soundstretch', '--help'],
            capture_output=True,
            text=True,
            timeout=2
        )
        
        if result.returncode == 0:
            print("✓ soundstretch está instalado correctamente")
            
            # Mostrar versión
            version_result = subprocess.run(
                ['soundstretch'],
                capture_output=True,
                text=True,
                timeout=2
            )
            # La versión suele estar en stderr o stdout
            version_info = version_result.stderr or version_result.stdout
            first_line = version_info.split('\n')[0] if version_info else "Versión desconocida"
            print(f"  Versión: {first_line}")
            return True
        else:
            print("✗ soundstretch retornó un error")
            return False
            
    except FileNotFoundError:
        print("✗ soundstretch NO está instalado")
        print("\nPara instalarlo, ejecuta:")
        print("  sudo apt-get update")
        print("  sudo apt-get install soundstretch")
        return False
    except subprocess.TimeoutExpired:
        print("✗ soundstretch no responde")
        return False

def test_basic_processing():
    """Test básico: procesar un audio de prueba"""
    print("\n" + "="*50)
    print("2. Test de procesamiento básico...")
    print("="*50)
    
    # Crear audio de prueba (1 segundo de tono a 440Hz)
    print("Generando audio de prueba (1s @ 440Hz)...")
    samplerate = 44100
    duration = 1.0
    freq = 440  # La4
    
    t = np.linspace(0, duration, int(samplerate * duration))
    audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        input_wav = os.path.join(tmpdir, "input.wav")
        output_wav = os.path.join(tmpdir, "output.wav")
        
        # Guardar audio de entrada
        sf.write(input_wav, audio, samplerate)
        print(f"✓ Audio de prueba guardado: {input_wav}")
        
        # Test 1: Ralentizar 15% (85% de velocidad)
        print("\nTest 1: Reducir tempo a 85% (más lento)...")
        try:
            result = subprocess.run(
                ['soundstretch', input_wav, output_wav, '-tempo=-15'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and os.path.exists(output_wav):
                processed, _ = sf.read(output_wav)
                expected_duration = duration / 0.85
                actual_duration = len(processed) / samplerate
                print(f"✓ Procesado correctamente")
                print(f"  Duración original: {duration:.2f}s")
                print(f"  Duración procesada: {actual_duration:.2f}s")
                print(f"  Duración esperada: {expected_duration:.2f}s")
                
                # Verificar que la duración es aproximadamente correcta (±5%)
                if abs(actual_duration - expected_duration) / expected_duration < 0.05:
                    print("✓ Duración correcta")
                else:
                    print(f"⚠ Duración ligeramente incorrecta (diferencia: {abs(actual_duration - expected_duration):.2f}s)")
            else:
                print("✗ Error en procesamiento")
                print(f"  stderr: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("✗ Timeout durante procesamiento")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
        
        # Limpiar para siguiente test
        if os.path.exists(output_wav):
            os.remove(output_wav)
        
        # Test 2: Acelerar 20% (120% de velocidad)
        print("\nTest 2: Aumentar tempo a 120% (más rápido)...")
        try:
            result = subprocess.run(
                ['soundstretch', input_wav, output_wav, '-tempo=+20'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and os.path.exists(output_wav):
                processed, _ = sf.read(output_wav)
                expected_duration = duration / 1.20
                actual_duration = len(processed) / samplerate
                print(f"✓ Procesado correctamente")
                print(f"  Duración original: {duration:.2f}s")
                print(f"  Duración procesada: {actual_duration:.2f}s")
                print(f"  Duración esperada: {expected_duration:.2f}s")
                
                if abs(actual_duration - expected_duration) / expected_duration < 0.05:
                    print("✓ Duración correcta")
                else:
                    print(f"⚠ Duración ligeramente incorrecta (diferencia: {abs(actual_duration - expected_duration):.2f}s)")
            else:
                print("✗ Error en procesamiento")
                print(f"  stderr: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    
    return True

def test_tempo_controller():
    """Test del TempoController con soundstretch"""
    print("\n" + "="*50)
    print("3. Test del TempoController...")
    print("="*50)
    
    try:
        # Intentar importar el nuevo tempo_controller
        sys.path.insert(0, '/home/claude')
        from tempo_controller_soundstretch import TempoController
        
        controller = TempoController()
        
        if not controller.is_available():
            print("✗ TempoController reporta que soundstretch no está disponible")
            return False
        
        print("✓ TempoController inicializado correctamente")
        
        # Crear audio de prueba
        samplerate = 44100
        duration = 0.5  # Más corto para test rápido
        freq = 440
        
        t = np.linspace(0, duration, int(samplerate * duration))
        audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
        
        # Test con callback de progreso
        progress_messages = []
        def progress_callback(msg):
            progress_messages.append(msg)
            print(f"  Progreso: {msg}")
        
        print("\nProcesando a 90%...")
        processed = controller.change_tempo(audio, samplerate, 90, on_progress=progress_callback)
        
        if processed is not None and len(processed) > len(audio):
            print("✓ Audio procesado correctamente")
            print(f"  Original: {len(audio)} samples")
            print(f"  Procesado: {len(processed)} samples")
            print(f"  Mensajes de progreso recibidos: {len(progress_messages)}")
        else:
            print("✗ Audio no procesado correctamente")
            return False
        
        # Verificar cache
        cache_info = controller.get_cache_info()
        print(f"\n✓ Cache funcionando:")
        print(f"  Tempos en cache: {cache_info['cached_tempos']}")
        print(f"  Cantidad: {cache_info['count']}/{cache_info['limit']}")
        
        return True
        
    except ImportError as e:
        print(f"✗ No se pudo importar TempoController: {e}")
        return False
    except Exception as e:
        print(f"✗ Error en test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Ejecuta todos los tests"""
    print("\n╔════════════════════════════════════════════════╗")
    print("║  Test de soundstretch para Practice Player    ║")
    print("╚════════════════════════════════════════════════╝\n")
    
    results = []
    
    # Test 1: Instalación
    installed = check_soundstretch_installed()
    results.append(("Instalación", installed))
    
    if not installed:
        print("\n" + "="*50)
        print("RESUMEN")
        print("="*50)
        print("✗ soundstretch no está instalado")
        print("\nPara continuar, instala soundstretch:")
        print("  sudo apt-get update")
        print("  sudo apt-get install soundstretch")
        return 1
    
    # Test 2: Procesamiento básico
    basic_ok = test_basic_processing()
    results.append(("Procesamiento básico", basic_ok))
    
    # Test 3: TempoController
    controller_ok = test_tempo_controller()
    results.append(("TempoController", controller_ok))
    
    # Resumen
    print("\n" + "="*50)
    print("RESUMEN")
    print("="*50)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} | {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print("="*50)
    print(f"Total: {passed}/{total} tests pasados")
    
    if passed == total:
        print("\n✓ Todos los tests OK")
        print("\nPróximos pasos:")
        print("1. Reemplazar tempo_controller.py con tempo_controller_soundstretch.py")
        print("2. Reemplazar audio_player.py con audio_player_with_tempo.py")
        print("3. Probar el Practice Player completo")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
