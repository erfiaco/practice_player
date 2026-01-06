import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time

class AudioPlayer:
    """
    Reproductor de audio con loop A-B y control de tempo
    """
    
    def __init__(self, on_state_change=None):
        self.filepath = None
        self.audio_data = None
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
        self.processed_audio = None  # Audio con tempo aplicado
        
        # Threading
        self.playback_thread = None
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
            self.audio_data, self.samplerate = sf.read(filepath)
            self.filepath = filepath
            self.duration = len(self.audio_data) / self.samplerate
            
            # Reset de estado
            self.current_position = 0.0
            self.point_a = None
            self.point_b = None
            self.tempo_percent = 100
            self.processed_audio = None
            
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
        print("Modo ajuste punto A (±0.1s)")
    
    def start_adjusting_b(self):
        """Entra en modo ajuste de punto B"""
        if self.point_b is None:
            print("⚠ Primero marca el punto B")
            return
        
        self.adjusting_point = 'B'
        self.pause()
        print("Modo ajuste punto B (±0.1s)")
    
    def adjust_fine(self, delta):
        """
        Ajusta el punto activo en ±delta segundos
        delta: típicamente ±0.1
        """
        if self.adjusting_point == 'A' and self.point_a is not None:
            self.point_a = max(0, min(self.duration, self.point_a + delta))
            print(f"Punto A ajustado: {self.point_a:.3f}s")
            
        elif self.adjusting_point == 'B' and self.point_b is not None:
            self.point_b = max(0, min(self.duration, self.point_b + delta))
            print(f"Punto B ajustado: {self.point_b:.3f}s")
    
    def finish_adjusting(self):
        """Sale del modo ajuste"""
        self.adjusting_point = None
        self.resume()
    
    # ========== TEMPO ==========
    
    def change_tempo(self, delta_percent):
        """
        Cambia el tempo en ±delta_percent
        delta_percent: típicamente ±1
        """
        old_tempo = self.tempo_percent
        self.tempo_percent = max(50, min(200, self.tempo_percent + delta_percent))
        
        if old_tempo != self.tempo_percent:
            print(f"Tempo: {self.tempo_percent}%")
            
            # Si está reproduciendo, hay que reprocesar
            if self.is_playing:
                self._apply_tempo_to_section()
            
            if self.on_state_change:
                self.on_state_change(f"Tempo: {self.tempo_percent}%")
    
    def _apply_tempo_to_section(self):
        """
        Aplica time-stretching a la sección actual
        TODO: Implementar con pyrubberband en siguiente paso
        """
        # Por ahora solo placeholder
        # En el siguiente archivo implementaremos tempo_controller.py
        pass
    
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
        # Convertir tiempos a samples
        start_sample = int(start_time * self.samplerate)
        end_sample = int(end_time * self.samplerate)
        
        # Extraer sección
        section = self.audio_data[start_sample:end_sample]
        
        # TODO: Aplicar tempo si es necesario
        
        # Reproducir
        self.current_position = start_time
        sd.play(section, self.samplerate)
        
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
                    remaining_section = self.audio_data[remaining_start:end_sample]
                    sd.play(remaining_section, self.samplerate)
            
            # Actualizar posición
            if sd.get_stream().active:
                elapsed = sd.get_stream().time
                self.current_position = start_time + elapsed
            
            time.sleep(0.05)
        
        sd.wait()
    
    # ========== GETTERS ==========
    
    def get_state(self):
        """Retorna 'PLAYING', 'PAUSED', o 'STOPPED'"""
        if self.is_playing and not self.is_paused:
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
