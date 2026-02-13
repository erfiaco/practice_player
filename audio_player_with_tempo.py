"""
Audio Player - Reproductor con loop A-B y control de tempo

CAMBIOS PARA TEMPO:
- change_tempo() ahora procesa de forma asíncrona
- Auto-pause cuando se cambia tempo
- Callback para reportar progreso al display
- Cache de audio procesado
"""

import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
from tempo_controller import TempoController

class AudioPlayer:
    """
    Reproductor de audio con loop A-B y control de tempo
    """
    
    def __init__(self, on_state_change=None):
        self.filepath = None
        self.audio_data = None  # Audio original sin modificar
        self.samplerate = None
        self.duration = 0.0
        
        # Estado de reproducción
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0  # Posición en segundos
        
        # Loop A-B
        self.point_a = None
        self.point_b = None
        
        # Tempo
        self.tempo_percent = 100  # 100% = velocidad normal
        self.tempo_controller = TempoController()
        self.processed_audio = None  # Audio con tempo aplicado
        self.is_processing_tempo = False  # Flag para indicar procesamiento en curso
        
        # Threading
        self.playback_thread = None
        self.tempo_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Callback para notificar cambios
        self.on_state_change = on_state_change
        
        # Ajuste fino (para hold)
        self.adjusting_point = None  # 'A' o 'B' cuando estamos ajustando
        
    # ========== CARGA DE ARCHIVO ==========
    
    def load_file(self, filepath):
        """Carga un archivo WAV en memoria"""
        try:
            self.stop()  # Detener reproducción anterior
            
            print(f"Cargando: {filepath}")
            self.audio_data, self.samplerate = sf.read(filepath, dtype='float32')
            self.filepath = filepath
            self.duration = len(self.audio_data) / self.samplerate
            
            # Reset de estado
            self.current_position = 0.0
            self.point_a = None
            self.point_b = None
            self.tempo_percent = 100
            self.processed_audio = None
            self.tempo_controller.clear_cache()
            
            print(f"✓ Cargado: {self.duration:.1f}s @ {self.samplerate}Hz")
            
            if self.on_state_change:
                self.on_state_change("Archivo cargado")
            
            return True
            
        except Exception as e:
            print(f"Error al cargar {filepath}: {e}")
            return False
    
    # ========== REPRODUCCIÓN ==========
    
    def play(self):
        """Inicia o resume la reproducción"""
        if self.audio_data is None:
            print("⚠ No hay archivo cargado")
            return
        
        if self.is_playing:
            return
        
        # ⭐ Solo resetear posición si NO estamos resumiendo desde pausa
        if not self.is_paused:
            self.current_position = 0.0
        
        self.is_playing = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Lanzar thread de reproducción
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def pause(self):
        """Pausa la reproducción"""
        if not self.is_playing or self.is_paused:
            return
        
        self.is_paused = True
        self.pause_event.set()
        sd.stop()
        
        if self.on_state_change:
            self.on_state_change("Pausado")
    
    def resume(self):
        """Resume después de pausa"""
        if not self.is_paused:
            return
        
        self.is_paused = False
        self.pause_event.clear()
        
        # ⭐ Si el thread murió, relanzarlo
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.is_playing = True
            self.stop_event.clear()
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def stop(self):
        """Detiene completamente la reproducción"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self.is_paused = False
        self.stop_event.set()
        self.pause_event.set()
        sd.stop()
        
        # Esperar a que termine el thread
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        
        # ⭐ Resetear posición al detener
        self.current_position = 0.0
        
        if self.on_state_change:
            self.on_state_change("Detenido")
    
    def toggle_play_pause(self):
        """Alterna entre play y pause"""
        if self.is_playing and not self.is_paused:
            self.pause()
        elif self.is_paused:
            self.resume()
        else:
            self.play()
    
    # ========== PLAYBACK WORKER ==========
    
    def _playback_worker(self):
        """Thread de reproducción (loop infinito)"""
        try:
            while not self.stop_event.is_set():
                # Determinar qué reproducir
                if self.point_a is not None and self.point_b is not None:
                    # Modo loop A-B
                    self._play_section(self.point_a, self.point_b)
                else:
                    # Reproducción normal
                    self._play_section(0, self.duration)
                
                # Si no estamos en loop, terminar
                if self.point_a is None or self.point_b is None:
                    break
        
        except Exception as e:
            print(f"Error en playback: {e}")
        
        finally:
            sd.stop()
            self.is_playing = False
    
    def _play_section(self, start_time, end_time):
        """Reproduce una sección específica del audio"""
        # ⭐ Si current_position está entre start_time y end_time, resumir desde ahí
        if start_time < self.current_position < end_time:
            actual_start = self.current_position
        else:
            actual_start = start_time
            self.current_position = start_time
        
        # Elegir qué audio usar (original o procesado)
        audio_to_play = self.processed_audio if self.processed_audio is not None else self.audio_data
        
        # Convertir tiempos a samples
        start_sample = int(actual_start * self.samplerate)
        end_sample = int(end_time * self.samplerate)
        
        # Ajustar índices si el audio procesado tiene diferente longitud
        if self.processed_audio is not None:
            # Calcular ratio de tiempo
            original_duration = len(self.audio_data) / self.samplerate
            processed_duration = len(self.processed_audio) / self.samplerate
            time_ratio = processed_duration / original_duration
            
            # Ajustar samples
            start_sample = int(start_sample * time_ratio)
            end_sample = int(end_sample * time_ratio)
        
        # Extraer sección
        section = audio_to_play[start_sample:end_sample]
        
        # Reproducir
        playback_start_time = time.perf_counter()
        sd.play(section, self.samplerate)
        time.sleep(0.01)  # ⭐ Pequeño delay para que el stream se inicialice
        
        # Actualizar posición mientras reproduce
        while sd.get_stream().active and not self.stop_event.is_set():
            # Manejar pausa
            if self.pause_event.is_set():
                sd.stop()
                # Esperar a que se quite la pausa
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    time.sleep(0.05)
                # Reanudar desde donde estábamos
                if not self.stop_event.is_set():
                    remaining_start = int(self.current_position * self.samplerate)
                    if self.processed_audio is not None:
                        time_ratio = (len(self.processed_audio) / self.samplerate) / (len(self.audio_data) / self.samplerate)
                        remaining_start = int(remaining_start * time_ratio)
                    remaining_section = audio_to_play[remaining_start:end_sample]
                    playback_start_time = time.perf_counter()
                    sd.play(remaining_section, self.samplerate)
                    time.sleep(0.01)
            
            # Actualizar posición
            if sd.get_stream().active:
                elapsed = time.perf_counter() - playback_start_time
                self.current_position = actual_start + elapsed
            
            time.sleep(0.05)
        
        sd.wait()
    
    # ========== TEMPO ==========
    
    def change_tempo(self, delta_percent):
        """
        Cambia el tempo en ±delta_percent
        
        Args:
            delta_percent: cambio en porcentaje (ej: -1, +1)
        """
        if self.audio_data is None:
            return
        
        # Calcular nuevo tempo
        new_tempo = self.tempo_percent + delta_percent
        new_tempo = max(50, min(200, new_tempo))  # Limitar 50-200%
        
        if new_tempo == self.tempo_percent:
            return
        
        self.tempo_percent = new_tempo
        print(f"Tempo: {self.tempo_percent}%")
        
        # ⭐ NUEVA LÓGICA: pausar si está reproduciendo
        was_playing = self.is_playing and not self.is_paused
        if was_playing:
            self.pause()
        
        # Procesar en thread separado para no bloquear
        if self.tempo_thread and self.tempo_thread.is_alive():
            print("⚠ Ya hay un procesamiento en curso")
            return
        
        self.tempo_thread = threading.Thread(
            target=self._process_tempo_async, 
            args=(new_tempo,),
            daemon=True
        )
        self.tempo_thread.start()
    
    def _process_tempo_async(self, tempo_percent):
        """Procesa el tempo en un thread separado"""
        self.is_processing_tempo = True
        
        # Callback de progreso
        def progress_callback(message):
            if self.on_state_change:
                self.on_state_change(message)
        
        try:
            # Procesar audio completo (o sección A-B si está definida)
            if self.point_a is not None and self.point_b is not None:
                # Procesar solo sección A-B
                start_sample = int(self.point_a * self.samplerate)
                end_sample = int(self.point_b * self.samplerate)
                section = self.audio_data[start_sample:end_sample]
                
                processed_section = self.tempo_controller.change_tempo(
                    section, 
                    self.samplerate, 
                    tempo_percent,
                    on_progress=progress_callback
                )
                
                # Reconstruir audio completo con sección procesada
                self.processed_audio = np.concatenate([
                    self.audio_data[:start_sample],
                    processed_section,
                    self.audio_data[end_sample:]
                ])
            else:
                # Procesar todo el archivo
                self.processed_audio = self.tempo_controller.change_tempo(
                    self.audio_data, 
                    self.samplerate, 
                    tempo_percent,
                    on_progress=progress_callback
                )
            
            # Actualizar duración si cambió
            if self.processed_audio is not None:
                self.duration = len(self.processed_audio) / self.samplerate
            
        except Exception as e:
            print(f"Error procesando tempo: {e}")
            if self.on_state_change:
                self.on_state_change(f"Error: {e}")
        
        finally:
            self.is_processing_tempo = False
    
    # ========== LOOP A-B ==========
    
    def set_point_a(self):
        """Marca el punto A en la posición actual"""
        if self.audio_data is None:
            return
        
        self.point_a = self.current_position
        
        # Si B está antes de A, lo quitamos
        if self.point_b is not None and self.point_b < self.point_a:
            self.point_b = None
        
        print(f"Punto A marcado: {self.point_a:.1f}s")
        
        if self.on_state_change:
            self.on_state_change(f"Punto A: {self.point_a:.1f}s")
    
    def clear_point_a(self):
        """Desmarca el punto A"""
        self.point_a = None
        print("Punto A desmarcado")
        
        if self.on_state_change:
            self.on_state_change("Punto A desmarcado")
    
    def set_point_b(self):
        """Marca el punto B en la posición actual"""
        if self.audio_data is None:
            return
        
        self.point_b = self.current_position
        
        # Si A está después de B, lo quitamos
        if self.point_a is not None and self.point_a > self.point_b:
            self.point_a = None
        
        print(f"Punto B marcado: {self.point_b:.1f}s")
        
        if self.on_state_change:
            self.on_state_change(f"Punto B: {self.point_b:.1f}s")
    
    def clear_point_b(self):
        """Desmarca el punto B"""
        self.point_b = None
        print("Punto B desmarcado")
        
        if self.on_state_change:
            self.on_state_change("Punto B desmarcado")
    
    def toggle_point_a(self):
        """Marca/desmarca punto A según estado"""
        if self.point_a is None:
            self.set_point_a()
        else:
            self.clear_point_a()
    
    def toggle_point_b(self):
        """Marca/desmarca punto B según estado"""
        if self.point_b is None:
            self.set_point_b()
        else:
            self.clear_point_b()
    
    # ========== AJUSTE FINO ==========
    
    def start_adjusting_a(self):
        """Entra en modo ajuste de punto A"""
        if self.point_a is None:
            print("⚠ Primero marca el punto A")
            return
        
        self.adjusting_point = 'A'
        self.pause()
        
        if self.on_state_change:
            self.on_state_change("Ajustando punto A")
    
    def start_adjusting_b(self):
        """Entra en modo ajuste de punto B"""
        if self.point_b is None:
            print("⚠ Primero marca el punto B")
            return
        
        self.adjusting_point = 'B'
        self.pause()
        
        if self.on_state_change:
            self.on_state_change("Ajustando punto B")
    
    def adjust_point(self, delta_seconds):
        """Ajusta el punto activo en ±delta_seconds"""
        if self.adjusting_point == 'A' and self.point_a is not None:
            self.point_a += delta_seconds
            self.point_a = max(0, min(self.duration, self.point_a))
            
            if self.on_state_change:
                self.on_state_change(f"A: {self.point_a:.3f}s")
        
        elif self.adjusting_point == 'B' and self.point_b is not None:
            self.point_b += delta_seconds
            self.point_b = max(0, min(self.duration, self.point_b))
            
            if self.on_state_change:
                self.on_state_change(f"B: {self.point_b:.3f}s")
    
    def stop_adjusting(self):
        """Sale del modo ajuste"""
        self.adjusting_point = None
        
        if self.on_state_change:
            self.on_state_change("Ajuste finalizado")
    
    # ========== GETTERS ==========
    
    def get_state(self):
        """Retorna 'PLAYING', 'PAUSED', 'PROCESSING', o 'STOPPED'"""
        if self.is_processing_tempo:
            return 'PROCESSING'
        elif self.is_playing and not self.is_paused:
            return 'PLAYING'
        elif self.is_paused:
            return 'PAUSED'
        else:
            return 'STOPPED'
    
    def get_duration(self):
        """Retorna duración total del archivo"""
        return self.duration
    
    def get_current_time(self):
        """Retorna posición actual en segundos"""
        return self.current_position
    
    def get_tempo_percent(self):
        """Retorna tempo actual en porcentaje"""
        return self.tempo_percent
    
    def is_tempo_available(self):
        """Retorna True si tempo control está disponible"""
        return self.tempo_controller.is_available()
