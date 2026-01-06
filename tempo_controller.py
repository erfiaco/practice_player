"""
Tempo Controller - Time-stretching con Rubber Band Library

Este módulo maneja el cambio de tempo sin alterar el pitch.
Usa pyrubberband como wrapper de la Rubber Band Library (C++).
"""

import numpy as np

try:
    import pyrubberband as pyrb
    RUBBERBAND_AVAILABLE = True
except ImportError:
    RUBBERBAND_AVAILABLE = False
    print("⚠ pyrubberband no disponible - tempo change deshabilitado")

class TempoController:
    """
    Controlador de tempo con cache de versiones procesadas
    """
    
    def __init__(self):
        self.cache = {}  # {tempo_percent: processed_audio}
        self.cache_limit = 5  # Máximo de versiones en cache
        
    def change_tempo(self, audio_data, samplerate, tempo_percent):
        """
        Cambia el tempo del audio sin alterar el pitch
        
        Args:
            audio_data: numpy array del audio
            samplerate: sample rate del audio
            tempo_percent: porcentaje de tempo (100 = normal, 50 = mitad, 200 = doble)
        
        Returns:
            numpy array con audio procesado
        """
        if not RUBBERBAND_AVAILABLE:
            print("⚠ Rubber Band no disponible, retornando audio original")
            return audio_data
        
        # Si es 100%, no hacer nada
        if tempo_percent == 100:
            return audio_data
        
        # Revisar cache
        if tempo_percent in self.cache:
            print(f"✓ Usando audio cacheado ({tempo_percent}%)")
            return self.cache[tempo_percent]
        
        # Calcular time_stretch_ratio
        # ratio > 1 = más lento (más tiempo)
        # ratio < 1 = más rápido (menos tiempo)
        time_ratio = 100.0 / tempo_percent
        
        print(f"Procesando tempo: {tempo_percent}% (ratio={time_ratio:.2f})...")
        
        try:
            # pyrubberband.time_stretch(audio, samplerate, rate)
            # rate > 1 = más lento
            # rate < 1 = más rápido
            processed = pyrb.time_stretch(audio_data, samplerate, time_ratio)
            
            # Guardar en cache (si hay espacio)
            if len(self.cache) < self.cache_limit:
                self.cache[tempo_percent] = processed
            else:
                # Eliminar el más antiguo (simple FIFO)
                oldest_key = list(self.cache.keys())[0]
                del self.cache[oldest_key]
                self.cache[tempo_percent] = processed
            
            print(f"✓ Tempo procesado: {len(processed)/samplerate:.1f}s")
            return processed
            
        except Exception as e:
            print(f"Error en time-stretching: {e}")
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

# Función helper para uso directo
def apply_tempo(audio, samplerate, tempo_percent):
    """
    Función helper para aplicar tempo sin mantener cache
    """
    controller = TempoController()
    return controller.change_tempo(audio, samplerate, tempo_percent)


# === TESTING ===
if __name__ == "__main__":
    print("=== Tempo Controller Test ===")
    print(f"Rubber Band disponible: {RUBBERBAND_AVAILABLE}")
    
    if RUBBERBAND_AVAILABLE:
        # Crear audio de prueba (1 segundo de tono)
        import numpy as np
        samplerate = 44100
        duration = 1.0
        freq = 440  # La4
        
        t = np.linspace(0, duration, int(samplerate * duration))
        audio = np.sin(2 * np.pi * freq * t).astype(np.float32)
        
        controller = TempoController()
        
        # Test: 50% (mitad de velocidad)
        print("\nTest 1: 50% tempo (más lento)")
        slow = controller.change_tempo(audio, samplerate, 50)
        print(f"Original: {len(audio)/samplerate:.2f}s → Procesado: {len(slow)/samplerate:.2f}s")
        
        # Test: 200% (doble velocidad)
        print("\nTest 2: 200% tempo (más rápido)")
        fast = controller.change_tempo(audio, samplerate, 200)
        print(f"Original: {len(audio)/samplerate:.2f}s → Procesado: {len(fast)/samplerate:.2f}s")
        
        # Info de cache
        print(f"\nCache info: {controller.get_cache_info()}")
    else:
        print("\nPara habilitar tempo control, instala:")
        print("  sudo apt-get install rubberband-cli librubberband-dev")
        print("  pip3 install pyrubberband")
