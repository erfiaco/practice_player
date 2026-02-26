"""
Tempo Controller - Time-stretching con SoundStretch (SoundTouch Library)

Este módulo maneja el cambio de tempo sin alterar el pitch.
Usa soundstretch (SoundTouch) que es más eficiente que pyrubberband.

IMPORTANTE: No es tiempo real - requiere procesamiento previo.
"""

import subprocess
import tempfile
import os
import numpy as np
import soundfile as sf

class TempoController:
    """
    Controlador de tempo con procesamiento offline usando soundstretch
    """
    
    def __init__(self):
        self.cache = {}  # {tempo_percent: processed_audio_data}
        self.cache_limit = 10  # Máximo de versiones en cache
        self.soundstretch_available = self._check_soundstretch()
        
    def _check_soundstretch(self):
        """Verifica si soundstretch está instalado"""
        try:
            result = subprocess.run(
                ['soundstretch', '--help'], 
                capture_output=True, 
                timeout=2
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def change_tempo(self, audio_data, samplerate, tempo_percent, on_progress=None):
        """
        Cambia el tempo del audio sin alterar el pitch
        
        Args:
            audio_data: numpy array del audio
            samplerate: sample rate del audio
            tempo_percent: porcentaje de tempo (100 = normal, 50 = mitad, 200 = doble)
            on_progress: callback opcional(message) para reportar progreso
        
        Returns:
            numpy array con audio procesado
        """
        if not self.soundstretch_available:
            if on_progress:
                on_progress("⚠ soundstretch no disponible")
            print("⚠ soundstretch no disponible, retornando audio original")
            print("Instalar con: sudo apt-get install soundstretch")
            return audio_data
        
        # Si es 100%, no hacer nada
        if tempo_percent == 100:
            if on_progress:
                on_progress("Tempo 100% (sin cambios)")
            return audio_data
        
        # Revisar cache
        if tempo_percent in self.cache:
            if on_progress:
                on_progress(f"✓ Usando cache ({tempo_percent}%)")
            print(f"✓ Usando audio cacheado ({tempo_percent}%)")
            return self.cache[tempo_percent]
        
        # Calcular cambio de tempo para soundstretch
        # soundstretch usa: -tempo=X donde X es el cambio porcentual
        # tempo_percent=85 → queremos 85% de velocidad → -15% de tempo
        # tempo_percent=120 → queremos 120% de velocidad → +20% de tempo
        tempo_change = tempo_percent - 100
        
        if on_progress:
            on_progress(f"Processing {tempo_percent}%...")
        
        print(f"Procesando tempo: {tempo_percent}% (cambio={tempo_change:+d}%)...")

        if on_progress:
            on_progress(f"Processing {tempo_percent}%...")
        return processed
                
        # Crear archivos temporales
        with tempfile.TemporaryDirectory() as tmpdir:
            input_wav = os.path.join(tmpdir, "input.wav")
            output_wav = os.path.join(tmpdir, "output.wav")
            
            try:
                # Guardar audio de entrada
                sf.write(input_wav, audio_data, samplerate)
                
                # Ejecutar soundstretch
                # -tempo=X : cambio de tempo en porcentaje (-50 a +100)
                # -quick : procesamiento más rápido (menor calidad, pero OK para práctica)
                cmd = [
                    'soundstretch',
                    input_wav,
                    output_wav,
                    f'-tempo={tempo_change}'
                ]
                
                # Para tempos extremos, usar procesamiento rápido
                if abs(tempo_change) > 20:
                    cmd.append('-quick')
                
                if on_progress:
                    on_progress(f"Processing {tempo_percent}%...")
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30  # timeout de 30 segundos
                )
                
                if result.returncode != 0:
                    print(f"Error en soundstretch: {result.stderr}")
                    if on_progress:
                        on_progress("✗ Error procesando")
                    return audio_data
                
                # Leer audio procesado
                processed, _ = sf.read(output_wav, dtype='float32')
                
                # Guardar en cache
                if len(self.cache) >= self.cache_limit:
                    # Eliminar el más antiguo (simple FIFO)
                    oldest_key = list(self.cache.keys())[0]
                    del self.cache[oldest_key]
                
                self.cache[tempo_percent] = processed
                
                duration_in = len(audio_data) / samplerate
                duration_out = len(processed) / samplerate
                print(f"✓ Tempo procesado: {duration_in:.1f}s → {duration_out:.1f}s")
                
                if on_progress:
                    on_progress(f"✓ Ready at {tempo_percent}%")
                
                return processed
                
            except subprocess.TimeoutExpired:
                print("⚠ Timeout procesando audio (archivo muy largo)")
                if on_progress:
                    on_progress("✗ Timeout")
                return audio_data
            except Exception as e:
                print(f"Error en time-stretching: {e}")
                if on_progress:
                    on_progress(f"✗ Error: {e}")
                return audio_data
    
    def clear_cache(self):
        """Limpia el cache de audio procesado"""
        self.cache.clear()
        print("Cache de tempo limpiado")
    
    def get_cache_info(self):
        """Retorna información del cache"""
        return {
            'cached_tempos': list(self.cache.keys()),
            'count': len(self.cache),
            'limit': self.cache_limit
        }
    
    def is_available(self):
        """Retorna True si soundstretch está disponible"""
        return self.soundstretch_available


# Función helper para uso directo
def apply_tempo(audio, samplerate, tempo_percent, on_progress=None):
    """
    Función helper para aplicar tempo sin mantener cache
    """
    controller = TempoController()
    return controller.change_tempo(audio, samplerate, tempo_percent, on_progress)


# === TESTING ===
if __name__ == "__main__":
    print("=== Tempo Controller Test (soundstretch) ===")
    
    controller = TempoController()
    print(f"soundstretch disponible: {controller.is_available()}")
    
    if controller.is_available():
        # Crear audio de prueba (1 segundo de tono)
        import numpy as np
        samplerate = 44100
        duration = 1.0
        freq = 440  # La4
        
        t = np.linspace(0, duration, int(samplerate * duration))
        audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
        
        # Test: 85% (más lento)
        print("\nTest 1: 85% tempo (más lento)")
        slow = controller.change_tempo(audio, samplerate, 85)
        print(f"Original: {len(audio)/samplerate:.2f}s → Procesado: {len(slow)/samplerate:.2f}s")
        
        # Test: 120% (más rápido)
        print("\nTest 2: 120% tempo (más rápido)")
        fast = controller.change_tempo(audio, samplerate, 120)
        print(f"Original: {len(audio)/samplerate:.2f}s → Procesado: {len(fast)/samplerate:.2f}s")
        
        # Test cache
        print("\nTest 3: Cache hit (85% otra vez)")
        slow2 = controller.change_tempo(audio, samplerate, 85)
        
        # Info de cache
        print(f"\nCache info: {controller.get_cache_info()}")
    else:
        print("\nPara habilitar tempo control, instala:")
        print("  sudo apt-get install soundstretch")
