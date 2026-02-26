"""
Tempo Controller - Time-stretching con pyrubberband (versión asíncrona)
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
    Controlador de tempo con cache y procesamiento asíncrono
    """
    
    def __init__(self):
        self.cache = {}  # {tempo_percent: processed_audio}
        self.cache_limit = 10  # Máximo de versiones en cache
        
    def change_tempo(self, audio_data, samplerate, tempo_percent, on_progress=None):
        """
        Cambia el tempo del audio sin alterar el pitch
        
        IMPORTANTE: Este proceso NO es en tiempo real - puede tardar varios segundos
        
        Args:
            audio_data: numpy array del audio
            samplerate: sample rate del audio
            tempo_percent: porcentaje de tempo (100 = normal, 50 = mitad, 200 = doble)
            on_progress: callback opcional(message) para reportar progreso
        
        Returns:
            numpy array con audio procesado
        """
        if not RUBBERBAND_AVAILABLE:
            if on_progress:
                on_progress("⚠ pyrubberband no disponible")
            print("⚠ Rubber Band no disponible, retornando audio original")
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
        
        # Calcular time_stretch_ratio
        # ratio < 1 = más lento (más tiempo)
        # ratio > 1 = más rápido (menos tiempo)
        time_ratio = tempo_percent / 100.0 
        
        if on_progress:
            on_progress(f"Processing {tempo_percent}%...")
        
        print(f"Procesando tempo: {tempo_percent}% (ratio={time_ratio:.2f})...")
        print("⚠ Esto puede tardar 5-10 segundos...")
        
        try:
            # pyrubberband.time_stretch(audio, samplerate, rate)
            # rate > 1 = más lento
            # rate < 1 = más rápido
            processed = pyrb.time_stretch(audio_data, samplerate, time_ratio)
            
            # Guardar en cache (FIFO si está lleno)
            if len(self.cache) >= self.cache_limit:
                oldest_key = list(self.cache.keys())[0]
                del self.cache[oldest_key]
            
            self.cache[tempo_percent] = processed
            
            duration_in = len(audio_data) / samplerate
            duration_out = len(processed) / samplerate
            print(f"✓ Tempo procesado: {duration_in:.1f}s → {duration_out:.1f}s")
            
            if on_progress:
                on_progress(f"✓ Ready at {tempo_percent}%")
            
            return processed
            
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
        """Retorna True si pyrubberband está disponible"""
        return RUBBERBAND_AVAILABLE
