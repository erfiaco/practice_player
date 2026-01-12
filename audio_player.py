import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
from Audio_clip import AudioClip

class AudioPlayer:
    """
    Reproductor de audio con loop A-B y control de tempo
    """
    
    def __init__(self, on_state_change=None):
        self.filepath = None
        self.audio_data = None
        self.samplerate = None
        self.duration = 0.0
        
        # Estado de reproducciÃ³n
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0  # PosiciÃ³n en segundos
        
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
            self.stop()  # Detener reproducciÃ³n anterior
            
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
            
            print(f"âœ“ Cargado: {self.duration:.1f}s @ {self.samplerate}Hz")
            
            if self.on_state_change:
                self.on_state_change("Archivo cargado")
            
            return True
            
        except Exception as e:
            print(f"Error al cargar {filepath}: {e}")
            return False
    
    # ========== REPRODUCCIÃ“N ==========
    
    def play(self):
        """Inicia o resume la reproducciÃ³n"""
        if self.audio_data is None:
            print("âš  No hay archivo cargado")
            return
        
        if self.is_playing:
            return
        
        # â­ Solo resetear posiciÃ³n si NO estamos resumiendo desde pausa
        if not self.is_paused:
            self.current_position = 0.0
        
        self.is_playing = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Lanzar thread de reproducciÃ³n
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def pause(self):
        """Pausa la reproducciÃ³n"""
        if not self.is_playing or self.is_paused:
            return
        
        self.is_paused = True
        self.pause_event.set()
        sd.stop()
        
        if self.on_state_change:
            self.on_state_change("Pausado")
    
    def resume(self):
        """Resume despuÃ©s de pausa"""
        if not self.is_paused:
            return
        
        self.is_paused = False
        self.pause_event.clear()
        
        # â­ Si el thread muriÃ³, relanzarlo
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.is_playing = True
            self.stop_event.clear()
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def stop(self):
        """Detiene completamente la reproducciÃ³n"""
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
        
        # â­ Resetear posiciÃ³n al detener
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
    
    # ========== LOOP A-B ==========
    
    def set_point_a(self):
        """Marca el punto A en la posiciÃ³n actual"""
        if self.audio_data is None:
            return
        
        self.point_a = self.current_position
        
        # Si B estÃ¡ antes de A, lo quitamos
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
        """Marca el punto B en la posiciÃ³n actual"""
        if self.audio_data is None:
            return
        
        self.point_b = self.current_position
        
        # Si A estÃ¡ despuÃ©s de B, lo quitamos
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
        """Marca/desmarca punto A segÃºn estado"""
        if self.point_a is None:
            self.set_point_a()
        else:
            self.clear_point_a()
    
    def toggle_point_b(self):
        """Marca/desmarca punto B segÃºn estado"""
        if self.point_b is None:
            self.set_point_b()
        else:
            self.clear_point_b()
    
    # ========== AJUSTE FINO ==========
    
    def start_adjusting_a(self):
        """Entra en modo ajuste de punto A"""
        if self.point_a is None:
            print("âš  Primero marca el punto A")
            return
        
        self.adjusting_point = 'A'
        self.pause()
        print("Modo ajuste punto A (Â±0.1s)")
    
    def start_adjusting_b(self):
        """Entra en modo ajuste de punto B"""
        if self.point_b is None:
            print("âš  Primero marca el punto B")
            return
        
        self.adjusting_point = 'B'
        self.pause()
        print("Modo ajuste punto B (Â±0.1s)")
    
    def adjust_fine(self, delta):
        """
        Ajusta el punto activo en Â±delta segundos
        delta: tÃ­picamente Â±0.1
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
        Cambia el tempo en Â±delta_percent
        delta_percent: tÃ­picamente Â±1
        """
        old_tempo = self.tempo_percent
        self.tempo_percent = max(50, min(200, self.tempo_percent + delta_percent))
        
        if old_tempo != self.tempo_percent:
            print(f"Tempo: {self.tempo_percent}%")
            
            # Si estÃ¡ reproduciendo, hay que reprocesar
            if self.is_playing:
                self._apply_tempo_to_section()
            
            if self.on_state_change:
                self.on_state_change(f"Tempo: {self.tempo_percent}%")
    
    def _apply_tempo_to_section(self):
        """
        Aplica time-stretching a la secciÃ³n actual
        TODO: Implementar con pyrubberband en siguiente paso
        """
        # Por ahora solo placeholder
        # En el siguiente archivo implementaremos tempo_controller.py
        pass
    
    # ========== PLAYBACK WORKER ==========
    
    def _playback_worker(self):
        """Thread de reproducciÃ³n (loop infinito)"""
        try:
            while not self.stop_event.is_set():
                # Determinar quÃ© reproducir
                if self.point_a is not None and self.point_b is not None:
                    # Modo loop A-B
                    self._play_section(self.point_a, self.point_b)
                else:
                    # ReproducciÃ³n normal
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
        """Reproduce una secciÃ³n especÃ­fica del audio"""
        # â­ Si current_position estÃ¡ entre start_time y end_time, resumir desde ahÃ­
        # (esto pasa cuando se hace resume despuÃ©s de pause)
        if start_time < self.current_position < end_time:
            actual_start = self.current_position
        else:
            actual_start = start_time
            self.current_position = start_time
        
        # Convertir tiempos a samples
        start_sample = int(actual_start * self.samplerate)
        end_sample = int(end_time * self.samplerate)
        
        # Extraer secciÃ³n
        section = self.audio_data[start_sample:end_sample]
        
        # TODO: Aplicar tempo si es necesario
        
        # Reproducir
        playback_start_time = time.perf_counter()  # â­ Timestamp de inicio
        sd.play(section, self.samplerate)
        time.sleep(0.01)  # â­ PequeÃ±o delay para que el stream se inicialice
        
        # Actualizar posiciÃ³n mientras reproduce
        while sd.get_stream().active and not self.stop_event.is_set():
            # Manejar pausa
            if self.pause_event.is_set():
                sd.stop()
                # Esperar a que se quite la pausa
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    time.sleep(0.05)
                # Reanudar desde donde estÃ¡bamos
                if not self.stop_event.is_set():
                    remaining_start = int(self.current_position * self.samplerate)
                    remaining_section = self.audio_data[remaining_start:end_sample]
                    playback_start_time = time.perf_counter()  # â­ Reset timestamp
                    sd.play(remaining_section, self.samplerate)
                    time.sleep(0.01)  # â­ Delay para inicializaciÃ³n del stream
            
            # Actualizar posiciÃ³n usando perf_counter en vez de sd.get_stream().time
            if sd.get_stream().active:
                elapsed = time.perf_counter() - playback_start_time  # â­ Calcular elapsed
                self.current_position = actual_start + elapsed
            
            time.sleep(0.05)
        
        sd.wait()
    
    # ========== GUARDAR LOOP ==========
    
    def save_loop(self):
        """
        Guarda la sección A-B como un nuevo archivo WAV
        Formato: nombreoriginal_MMSS.wav (donde MMSS es el minuto:segundo del punto A)
        Retorna: (success, mensaje)
        """
        # Verificar que hay loop definido
        if self.point_a is None or self.point_b is None:
            return (False, "No hay loop A-B definido")
        
        if self.audio_data is None or self.filepath is None:
            return (False, "No hay archivo cargado")
        
        try:
            # Extraer nombre base del archivo original (sin path ni extensión)
            import os
            basename = os.path.basename(self.filepath)  # ej: "solo_django.wav"
            name_without_ext = os.path.splitext(basename)[0]  # ej: "solo_django"
            
            # Calcular minuto y segundo del punto A
            minutes = int(self.point_a // 60)
            seconds = int(self.point_a % 60)
            timestamp = f"{minutes:02d}{seconds:02d}"  # ej: "0205" para 2:05
            
            # Construir nuevo nombre
            new_basename = f"{name_without_ext}_{timestamp}.wav"
            
            # Path completo (misma carpeta que el original)
            original_dir = os.path.dirname(self.filepath)
            new_filepath = os.path.join(original_dir, new_basename)
            
            # Verificar si ya existe
            if os.path.exists(new_filepath):
                # Añadir sufijo numérico
                counter = 1
                while os.path.exists(new_filepath):
                    new_basename = f"{name_without_ext}_{timestamp}_{counter}.wav"
                    new_filepath = os.path.join(original_dir, new_basename)
                    counter += 1
            
            # Extraer sección de audio
            start_sample = int(self.point_a * self.samplerate)
            end_sample = int(self.point_b * self.samplerate)
            loop_section = self.audio_data[start_sample:end_sample]
            
            # Guardar como WAV
            #sf.write(new_filepath, loop_section, self.samplerate)
            AudioClip(new_filepath, loop_section, self.samplerate)
            duration = (self.point_b - self.point_a)
            print(f"✓ Loop guardado: {new_basename} ({duration:.1f}s)")
            
            return (True, f"Guardado: {new_basename}")
            
        except Exception as e:
            print(f"Error al guardar loop: {e}")
            return (False, f"Error: {e}")
    
    # ========== GUARDAR LOOP ==========
    
    def save_loop(self):
        """
        Guarda la sección A-B como un nuevo archivo WAV
        Formato: nombreoriginal_MMSS.wav (donde MMSS es el minuto:segundo del punto A)
        Retorna: (success, mensaje)
        """
        # Verificar que hay loop definido
        if self.point_a is None or self.point_b is None:
            return (False, "No loop A-B")
        
        if self.audio_data is None or self.filepath is None:
            return (False, "No hay archivo")
        
        try:
            # Extraer nombre base del archivo original (sin path ni extensión)
            import os
            basename = os.path.basename(self.filepath)  # ej: "solo_django.wav"
            name_without_ext = os.path.splitext(basename)[0]  # ej: "solo_django"
            
            # Calcular minuto y segundo del punto A
            minutes = int(self.point_a // 60)
            seconds = int(self.point_a % 60)
            timestamp = f"{minutes:02d}{seconds:02d}"  # ej: "0205" para 2:05
            
            # Construir nuevo nombre
            new_basename = f"{name_without_ext}_{timestamp}.wav"
            
            # Path completo (misma carpeta que el original)
            original_dir = os.path.dirname(self.filepath)
            new_filepath = os.path.join(original_dir, new_basename)
            
            # Verificar si ya existe y añadir sufijo si es necesario
            if os.path.exists(new_filepath):
                counter = 1
                while os.path.exists(new_filepath):
                    new_basename = f"{name_without_ext}_{timestamp}_{counter}.wav"
                    new_filepath = os.path.join(original_dir, new_basename)
                    counter += 1
            
            # Extraer sección de audio
            start_sample = int(self.point_a * self.samplerate)
            end_sample = int(self.point_b * self.samplerate)
            loop_section = self.audio_data[start_sample:end_sample]
            
            # Guardar como WAV
            sf.write(new_filepath, loop_section, self.samplerate)
            
            duration = (self.point_b - self.point_a)
            print(f"✓ Loop guardado: {new_basename} ({duration:.1f}s)")
            
            return (True, new_basename)
            
        except Exception as e:
            print(f"Error al guardar loop: {e}")
            return (False, f"Error: {str(e)[:20]}")
    
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
        """Retorna duraciÃ³n total del archivo"""
        return self.duration
    
    def get_current_time(self):
        """Retorna posiciÃ³n actual en segundos"""
        return self.current_position
