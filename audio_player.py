import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
from tempo_controller import TempoController
sd.default.device = 0  # AudioInjector (hw:1,0)

class AudioPlayer:
    """
    Reproductor de audio con loop A-B y control de tempo
    """
    
    def __init__(self, on_state_change=None):
        self.filepath = None
        self.audio_data = None
        self.samplerate = None
        self.duration = 0.0
        
        
        # Estado de reproducciÃƒÂ³n
        self.is_playing = False
        self.is_paused = False
        self.current_position = 0.0  # PosiciÃƒÂ³n en segundos
        
        # Loop A-B
        self.point_a = None
        self.point_b = None
        
        # Tempo
        self.tempo_percent = 100  # 100% = velocidad normal
        self.tempo_controller = TempoController()  # ⭐ AÑADIR ESTA LÍNEA
        self.processed_audio = None  # Audio con tempo aplicado
        
        # Threading
        self.playback_thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.sd_lock = threading.Lock()
        
        # Callback para notificar cambios
        self.on_state_change = on_state_change
        
        # Ajuste fino (para hold)
        self.adjusting_point = None  # 'A' o 'B' cuando estamos ajustando
        
    # ========== CARGA DE ARCHIVO ==========
    
    def load_file(self, filepath):
        """Carga un archivo WAV en memoria"""
        try:
            self.stop()  # Detener reproducciÃƒÂ³n anterior
            
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
            
            print(f"Ã¢Å“â€œ Cargado: {self.duration:.1f}s @ {self.samplerate}Hz")
            
            if self.on_state_change:
                self.on_state_change("Archivo cargado")
            
            return True
            
        except Exception as e:
            print(f"Error al cargar {filepath}: {e}")
            return False
    
    # ========== REPRODUCCIÃƒâ€œN ==========
   
    
    def play(self):
        """Inicia o resume la reproducciÃƒÂ³n"""
        if self.audio_data is None:
            print("Ã¢Å¡Â  No hay archivo cargado")
            return
        
        if self.is_playing:
            return
            
    
        # Si el tempo cambió y no está en cache, procesar antes de reproducir
        if self.tempo_percent != 100:
            if self.tempo_percent not in self.tempo_controller.cache:
                if self.on_state_change:
                    self.on_state_change(f"Processing {self.tempo_percent}%...")
                self._process_tempo_sync()
        elif self.tempo_percent == 100:
            # Si volvemos a 100%, usar audio original
            self.processed_audio = None
        
        # Ã¢Â­Â Solo resetear posiciÃƒÂ³n si NO estamos resumiendo desde pausa
        if not self.is_paused:
            self.current_position = 0.0
        
        self.is_playing = True
        self.is_paused = False
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Lanzar thread de reproducciÃƒÂ³n
        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def pause(self):
        """Pausa la reproducciÃƒÂ³n"""
        if not self.is_playing or self.is_paused:
            return
        
        self.is_paused = True
        self.pause_event.set()
        with self.sd_lock:
            sd.stop()
        
        if self.on_state_change:
            self.on_state_change("Pausado")
    
    def resume(self):
        """Resume despuÃƒÂ©s de pausa"""
        if not self.is_paused:
            return
        
        self.is_paused = False
        self.pause_event.clear()
        
        # Ã¢Â­Â Si el thread muriÃƒÂ³, relanzarlo
        if self.playback_thread is None or not self.playback_thread.is_alive():
            self.is_playing = True
            self.stop_event.clear()
            self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
            self.playback_thread.start()
        
        if self.on_state_change:
            self.on_state_change("Reproduciendo")
    
    def stop(self):
        """Detiene completamente la reproducciÃƒÂ³n"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self.is_paused = False
        self.stop_event.set()
        self.pause_event.set()
        with self.sd_lock:
            sd.stop()
        
        # Esperar a que termine el thread
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)
        
        # Ã¢Â­Â Resetear posiciÃƒÂ³n al detener
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


    # ========== TEMPO PROCESSING ==========
    
    def _process_tempo_sync(self):
        """
        Procesa tempo de forma síncrona (bloquea hasta terminar)
        Se llama desde play() cuando es necesario
        """
        def progress_callback(message):
            if self.on_state_change:
                self.on_state_change(message)
        
        try:
            # Procesar audio completo
            self.processed_audio = self.tempo_controller.change_tempo(
                self.audio_data,
                self.samplerate,
                self.tempo_percent,
                on_progress=progress_callback
            )
            
        except Exception as e:
            print(f"Error procesando tempo: {e}")
            if self.on_state_change:
                self.on_state_change(f"Error: {e}")
            self.processed_audio = None



    
    # ========== LOOP A-B ==========
    
    def set_point_a(self):
        """Marca el punto A en la posiciÃƒÂ³n actual"""
        if self.audio_data is None:
            return
        
        self.point_a = self.current_position
        
        # Si B estÃƒÂ¡ antes de A, lo quitamos
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
        """Marca el punto B en la posiciÃƒÂ³n actual"""
        if self.audio_data is None:
            return
        
        self.point_b = self.current_position
        
        # Si A estÃƒÂ¡ despuÃƒÂ©s de B, lo quitamos
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
        """Marca/desmarca punto A segÃƒÂºn estado"""
        if self.point_a is None:
            self.set_point_a()
        else:
            self.clear_point_a()
    
    def toggle_point_b(self):
        """Marca/desmarca punto B segÃƒÂºn estado"""
        if self.point_b is None:
            self.set_point_b()
        else:
            self.clear_point_b()
    
    # ========== AJUSTE FINO ==========
    
    def start_adjusting_a(self):
        """Entra en modo ajuste de punto A"""
        if self.point_a is None:
            print("Ã¢Å¡Â  Primero marca el punto A")
            return
        
        self.adjusting_point = 'A'
        self.pause()
        print("Modo ajuste punto A (Ã‚Â±0.1s)")
    
    def start_adjusting_b(self):
        """Entra en modo ajuste de punto B"""
        if self.point_b is None:
            print("Ã¢Å¡Â  Primero marca el punto B")
            return
        
        self.adjusting_point = 'B'
        self.pause()
        print("Modo ajuste punto B (Ã‚Â±0.1s)")
    
    def start_adjusting_position(self):
        """Entra en modo ajuste de posiciÃƒÂ³n de reproducciÃƒÂ³n"""
        if not self.is_paused:
            print("Ã¢Å¡  Pausa primero para ajustar la posiciÃƒÂ³n")
            return
        
        self.adjusting_point = 'POSITION'
        print("Modo ajuste posiciÃƒÂ³n (Ã‚Â±0.1s)")
        
        if self.on_state_change:
            self.on_state_change("Ajustando posiciÃƒÂ³n")
    
    def adjust_fine(self, delta):
        """
        Ajusta el punto activo en Ã‚Â±delta segundos
        delta: tÃƒÂ­picamente Ã‚Â±0.1
        """
        if self.adjusting_point == 'A' and self.point_a is not None:
            self.point_a = max(0, min(self.duration, self.point_a + delta))
            print(f"Punto A ajustado: {self.point_a:.3f}s")
            
        elif self.adjusting_point == 'B' and self.point_b is not None:
            self.point_b = max(0, min(self.duration, self.point_b + delta))
            print(f"Punto B ajustado: {self.point_b:.3f}s")
            
        elif self.adjusting_point == 'POSITION':
            self.current_position = max(0, min(self.duration, self.current_position + delta))
            print(f"PosiciÃƒÂ³n ajustada: {self.current_position:.3f}s")
    
    def finish_adjusting(self):
        """Sale del modo ajuste"""
        was_position = (self.adjusting_point == 'POSITION')
        self.adjusting_point = None
        
        # Solo resumir automÃƒÂ¡ticamente si no estÃƒÂ¡bamos ajustando posiciÃƒÂ³n
        # (para posiciÃƒÂ³n, el usuario debe pulsar play cuando estÃƒÂ© listo)
        if not was_position:
            self.resume()
    
    # ========== TEMPO ==========
    
    def change_tempo(self, delta_percent):
        """
        Cambia el tempo en ±delta_percent (solo actualiza el número)
        El procesamiento ocurre cuando se presiona play()
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
    
        if self.on_state_change:
            self.on_state_change(f"Tempo: {self.tempo_percent}%")    


    def _apply_tempo_to_section(self):
        """
        Aplica time-stretching a la secciÃƒÂ³n actual
        TODO: Implementar con pyrubberband en siguiente paso
        """
        # Por ahora solo placeholder
        # En el siguiente archivo implementaremos tempo_controller.py
        pass
    
    # ========== PLAYBACK WORKER ==========
    
    def _playback_worker(self):
        """Thread de reproducciÃƒÂ³n (loop infinito)"""
        try:
            while not self.stop_event.is_set():
                # Determinar quÃƒÂ© reproducir
                if self.point_a is not None and self.point_b is not None:
                    # Modo loop A-B
                    self._play_section(self.point_a, self.point_b)
                else:
                    # ReproducciÃƒÂ³n normal
                    self._play_section(0, self.duration)
                
                # Si no estamos en loop, terminar
                if self.point_a is None or self.point_b is None:
                    break
        
        except Exception as e:
            print(f"Error en playback: {e}")
        
        finally:
            with self.sd_lock:
                sd.stop()
            self.is_playing = False
    
    def _play_section(self, start_time, end_time):
        """Reproduce una secciÃƒÂ³n especÃƒÂ­fica del audio"""
        # Ã¢Â­Â Si current_position estÃƒÂ¡ entre start_time y end_time, resumir desde ahÃƒÂ­
        # (esto pasa cuando se hace resume despuÃƒÂ©s de pause)
        if start_time < self.current_position < end_time:
            actual_start = self.current_position
        else:
            actual_start = start_time
            self.current_position = start_time
        
        # Convertir tiempos a samples
        start_sample = int(actual_start * self.samplerate)
        end_sample = int(end_time * self.samplerate)
        
        # Extraer secciÃƒÂ³n
        section = self.audio_data[start_sample:end_sample]
        
        # TODO: Aplicar tempo si es necesario
        
        # Reproducir
        playback_start_time = time.perf_counter()  # Ã¢Â­Â Timestamp de inicio
        with self.sd_lock:
            sd.play(section, self.samplerate, device=0)
        time.sleep(0.01)  # Ã¢Â­Â PequeÃƒÂ±o delay para que el stream se inicialice
        
        # Actualizar posiciÃƒÂ³n mientras reproduce
        while sd.get_stream().active and not self.stop_event.is_set():
            # Manejar pausa
            if self.pause_event.is_set():
                with self.sd_lock:
                    sd.stop()
                # Esperar a que se quite la pausa
                while self.pause_event.is_set() and not self.stop_event.is_set():
                    time.sleep(0.05)
                # Reanudar desde donde estÃƒÂ¡bamos
                if not self.stop_event.is_set():
                    remaining_start = int(self.current_position * self.samplerate)
                    remaining_section = self.audio_data[remaining_start:end_sample]
                    playback_start_time = time.perf_counter()  # Ã¢Â­Â Reset timestamp
                    with self.sd_lock:
                        sd.play(remaining_section, self.samplerate, device=0)
                    time.sleep(0.01)  # Ã¢Â­Â Delay para inicializaciÃƒÂ³n del stream
            
            # Actualizar posiciÃƒÂ³n usando perf_counter en vez de sd.get_stream().time
            if sd.get_stream().active:
                elapsed = time.perf_counter() - playback_start_time  # Ã¢Â­Â Calcular elapsed
                self.current_position = actual_start + elapsed
            
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
        """Retorna duraciÃƒÂ³n total del archivo"""
        return self.duration
    
    def get_current_time(self):
        """Retorna posiciÃƒÂ³n actual en segundos"""
        return self.current_position
    
    def save_loop(self, output_dir="audio_files"):
        """
        Guarda la secciÃƒÂ³n A-B como nuevo archivo WAV
        Nombre: Nombre_original_mm-ss.wav (donde mm-ss es el punto A)
        
        Returns:
            str: nombre del archivo guardado, o None si falla
        """
        import os
        from datetime import datetime
        
        # Validar que existan puntos A y B
        if self.point_a is None or self.point_b is None:
            print("âš  No se puede guardar: marca primero los puntos A y B")
            return None
        
        if self.audio_data is None:
            print("âš  No hay archivo cargado")
            return None
        
        # Generar nombre del archivo
        # Extraer nombre original sin extensiÃƒÂ³n
        if self.filepath:
            original_name = os.path.splitext(os.path.basename(self.filepath))[0]
        else:
            original_name = "loop"
        
        # Formatear punto A como mm-ss
        minutes = int(self.point_a // 60)
        seconds = int(self.point_a % 60)
        time_tag = f"{minutes:02d}-{seconds:02d}"
        
        # Nombre completo: original_mm-ss.wav
        output_filename = f"{original_name}_{time_tag}.wav"
        output_path = os.path.join(output_dir, output_filename)
        
        # Si ya existe, aÃƒÂ±adir sufijo
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{original_name}_{time_tag}_{counter}.wav"
            output_path = os.path.join(output_dir, output_filename)
            counter += 1
        
        try:
            # Extraer secciÃƒÂ³n A-B
            start_sample = int(self.point_a * self.samplerate)
            end_sample = int(self.point_b * self.samplerate)
            section = self.audio_data[start_sample:end_sample]
            
            # Aplicar tempo si es diferente de 100%
            if self.tempo_percent != 100:
                print(f"Aplicando tempo {self.tempo_percent}% al loop...")
                from tempo_controller import TempoController
                tempo_ctrl = TempoController()
                section = tempo_ctrl.change_tempo(section, self.samplerate, self.tempo_percent)
            
            # Guardar
            print(f"Guardando: {output_filename}")
            sf.write(output_path, section, self.samplerate)
            
            duration = len(section) / self.samplerate
            print(f"[Ok] Loop guardado: {output_filename} ({duration:.1f}s)")
            
            return output_filename
            
        except Exception as e:
            print(f"âœ— Error al guardar loop: {e}")
            import traceback
            traceback.print_exc()
            return None
