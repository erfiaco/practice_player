#!/usr/bin/env python3
"""
Practice Player - Reproductor para estudiar solos con loop A-B y control de tempo

Estados:
- BROWSER: SelecciÃƒÂ³n de archivos
- PLAYER: ReproducciÃƒÂ³n con controles
"""

import signal
import time
from threading import Event
from file_browser import FileBrowser
from audio_player import AudioPlayer
from buttons_manager import ButtonsManager
from oled_display import OledDisplay

import faulthandler, signal
faulthandler.register(signal.SIGUSR1)

class PracticePlayer:
    def __init__(self):
        self.exit_event = Event()
        self.state = 'BROWSER'  # Estado inicial
        
        # Componentes
        self.display = OledDisplay()
        self.browser = FileBrowser(audio_dir="audio_files")
        self.player = AudioPlayer(on_state_change=self._update_ui)
        self.buttons = ButtonsManager()
        
        # Configurar botones segÃƒÂºn estado inicial
        self._set_browser_mode()
        
        # SeÃƒÂ±ales de sistema
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # UI refresh thread
        self.ui_refresh_active = True
        import threading
        self.ui_thread = threading.Thread(target=self._ui_refresh_loop, daemon=True)
        self.ui_thread.start()
    
    # ========== MÃƒÂQUINA DE ESTADOS ==========
    
    def _set_browser_mode(self):
        """Configura botones para modo BROWSER"""
        self.state = 'BROWSER'
        self.buttons.set_browser_mode(
            on_prev=self._browser_prev,
            on_next=self._browser_next,
            on_select=self._browser_select,
            on_exit=self._browser_exit
        )
        self._update_ui("Modo BROWSER")
        print("Ã¢â€ â€™ Modo BROWSER activado")
    
    def _set_player_mode(self):
        """Configura botones para modo PLAYER"""
        self.state = 'PLAYER'
        self.buttons.set_player_mode(
            on_play=self._player_play,
            on_play_hold=self._player_play_hold,
            on_mark_a_tap=self._player_mark_a_tap,
            on_mark_a_hold=self._player_mark_a_hold,
            on_mark_b_tap=self._player_mark_b_tap,
            on_mark_b_hold=self._player_mark_b_hold,
            on_stop=self._player_stop,
            on_back=self._player_back,
            on_tempo_down=self._player_tempo_down,
            on_tempo_up=self._player_tempo_up,
            on_save_loop=self._player_save_loop
        )
        self._update_ui("Modo PLAYER")
        print("Ã¢â€ â€™ Modo PLAYER activado")
    
    # ========== CALLBACKS BROWSER ==========
    
    def _browser_prev(self, delta=None):
        """GPIO23: Archivo anterior"""
        print("Ã¢â€ â€™ [BROWSER] Archivo anterior")
        self.browser.prev_file()
        self._update_ui()
    
    def _browser_next(self, delta=None):
        """GPIO22: Archivo siguiente"""
        print("Ã¢â€ â€™ [BROWSER] Archivo siguiente")
        self.browser.next_file()
        self._update_ui()
    
    def _browser_select(self):
        """GPIO13 TAP: Seleccionar archivo y pasar a PLAYER"""
        print("Ã¢â€ â€™ [BROWSER] Seleccionar archivo")
        
        if not self.browser.has_files():
            print("Ã¢Å¡Â  No hay archivos WAV disponibles")
            return
        
        filepath = self.browser.get_current_file()
        
        # Cargar archivo
        if self.player.load_file(filepath):
            # Cambiar a modo player
            self._set_player_mode()
        else:
            print("Ã¢Å¡Â  Error al cargar archivo")
    
    def _browser_exit(self):
        """GPIO13 HOLD: Salir del programa"""
        print("Ã¢â€ â€™ [BROWSER] Salir al boot menu")
        self.exit_event.set()
    
    # ========== CALLBACKS PLAYER ==========
    
    def _player_play(self):
        """GPIO5: Play/Pause"""
        print("Ã¢â€ â€™ [PLAYER] Play/Pause")
        
        # Si estamos ajustando, salir del modo ajuste
        if self.player.adjusting_point:
            self.player.finish_adjusting()
        else:
            self.player.toggle_play_pause()
        
        self._update_ui()
    
    def _player_play_hold(self):
        """GPIO5 HOLD: Entrar en modo ajuste de posiciÃƒÂ³n"""
        print("Ã¢â€ ' [PLAYER] Ajustar posiciÃƒÂ³n")
        self.player.start_adjusting_position()
        self._update_ui()
    
    def _player_mark_a_tap(self):
        """GPIO26 TAP: Marcar/desmarcar punto A"""
        print("Ã¢â€ â€™ [PLAYER] Toggle punto A")
        self.player.toggle_point_a()
        self._update_ui()
    
    def _player_mark_a_hold(self):
        """GPIO26 HOLD: Entrar en modo ajuste de punto A"""
        print("Ã¢â€ â€™ [PLAYER] Ajustar punto A")
        self.player.start_adjusting_a()
        self._update_ui()
    
    def _player_mark_b_tap(self):
        """GPIO6 TAP: Marcar/desmarcar punto B"""
        print("Ã¢â€ â€™ [PLAYER] Toggle punto B")
        self.player.toggle_point_b()
        self._update_ui()
    
    def _player_mark_b_hold(self):
        """GPIO6 HOLD: Entrar en modo ajuste de punto B"""
        print("Ã¢â€ â€™ [PLAYER] Ajustar punto B")
        self.player.start_adjusting_b()
        self._update_ui()
    
    def _player_stop(self):
        """GPIO13 TAP: Stop"""
        print("Ã¢â€ â€™ [PLAYER] Stop")
        self.player.stop()
        self._update_ui()
    
    def _player_back(self):
        """GPIO13 HOLD: Volver a BROWSER"""
        print("Ã¢â€ â€™ [PLAYER] Volver a BROWSER")
        self.player.stop()
        self._set_browser_mode()
    
    def _player_tempo_down(self, delta=0.1):
        """
        GPIO23: Tempo -1% o ajuste fino con delta variable
        delta: segundos a ajustar (0.1, 0.5, o 1.0 segÃƒÂºn tiempo pulsado)
        """
        if self.player.adjusting_point:
            # En modo ajuste: mover -delta segundos
            print(f"â†’ [PLAYER] Ajustar -{delta}s")
            self.player.adjust_fine(-delta)
        else:
            # Normal: tempo -1%
            print("Ã¢â€ â€™ [PLAYER] Tempo -1%")
            self.player.change_tempo(-1)
        
        self._update_ui()
    
    def _player_tempo_up(self, delta=0.1):
        """
        GPIO22: Tempo +1% o ajuste fino con delta variable
        delta: segundos a ajustar (0.1, 0.5, o 1.0 segÃºn tiempo pulsado)
        """
        if self.player.adjusting_point:
            # En modo ajuste: mover +delta segundos
            print(f"â†’ [PLAYER] Ajustar +{delta}s")
            self.player.adjust_fine(+delta)
        else:
            # Normal: tempo +1%
            print("Ã¢â€ â€™ [PLAYER] Tempo +1%")
            self.player.change_tempo(+1)
        
        self._update_ui()
    
    def _player_save_loop(self):
        """GPIO4: Guardar sección A-B como nuevo archivo"""
        print("✓ [PLAYER] Guardar loop")
        
        # Mostrar mensaje de procesamiento
        self.display.show_processing("Saving loop...")
        
        # Guardar el loop
        filename = self.player.save_loop(output_dir="audio_files")
        
        if filename:
            # Éxito - mostrar mensaje
            self.display.show_message(f"Saved: {filename}")
            time.sleep(2)
            
            # Refrescar browser para que aparezca el nuevo archivo
            self.browser.refresh()
            
            print(f"✓ Loop guardado como: {filename}")
        else:
            # Error
            self.display.show_message("Error: Check A-B points")
            time.sleep(2)
        
        # Volver a mostrar player UI
        self._update_ui()
    
    # ========== UI ==========
    
    def _update_ui(self, message=""):
        """Actualiza el display segÃƒÂºn el estado actual"""
        if message:
            print(f"[UI] {message}")
        
        # No hacer nada si estamos saliendo
        if self.exit_event.is_set():
            return
        
        # El update real se hace en el thread de UI refresh
        # para evitar sobrecarga en callbacks
    
    def _ui_refresh_loop(self):
        """Thread que actualiza el UI periÃƒÂ³dicamente"""
        while self.ui_refresh_active and not self.exit_event.is_set():
            try:
                if self.state == 'BROWSER':
                    self._render_browser_ui()
                elif self.state == 'PLAYER':
                    self._render_player_ui()
                
                time.sleep(0.1)  # 10 FPS es suficiente
                
            except Exception as e:
                print(f"Error en UI refresh: {e}")
                time.sleep(0.5)
    
    def _render_browser_ui(self):
        """Renderiza UI del browser"""
        filename = self.browser.get_current_filename()
        pos, total = self.browser.get_position()
        
        help_text = "SELECT=Load HOLD=Exit"
        
        self.display.show_browser(filename, pos, total, help_text)
    
    def _render_player_ui(self):
        """Renderiza UI del player"""
        # Si estamos ajustando un punto, mostrar pantalla especial
        if self.player.adjusting_point:
            if self.player.adjusting_point == 'A':
                point_value = self.player.point_a
            elif self.player.adjusting_point == 'B':
                point_value = self.player.point_b
            else:  # POSITION
                point_value = self.player.current_position
            
            self.display.show_adjusting(self.player.adjusting_point, point_value)
        else:
            # Pantalla normal de player
            state = self.player.get_state()
            current_time = self.player.get_current_time()
            total_time = self.player.get_duration()
            
            help_text = "PLAY A B STOP(3s)=Back"
            
            self.display.show_player(
                state=state,
                current_time=current_time,
                total_time=total_time,
                point_a=self.player.point_a,
                point_b=self.player.point_b,
                tempo=self.player.tempo_percent,
                help_text=help_text
            )
    
    # ========== SEÃƒâ€˜ALES ==========
    
    def _signal_handler(self, signum, frame):
        print("\nSeÃƒÂ±al recibida Ã¢â€ â€™ Saliendo limpiamente")
        self.exit_event.set()
    
    # ========== RUN & CLEANUP ==========
    
    def run(self):
        """Loop principal"""
        print("=== Practice Player ===")
        print(f"Archivos disponibles: {self.browser.get_file_count()}")
        
        self._update_ui("Listo")
        
        try:
            while not self.exit_event.is_set():
                time.sleep(0.1)
        
        except KeyboardInterrupt:
            print("\nInterrupciÃƒÂ³n de teclado")
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpieza de recursos"""
        print("Limpiando recursos...")
        
        self.ui_refresh_active = False
        self.player.stop()
        self.display.clear()
        self.buttons.close()
        
        print("Ã‚Â¡AdiÃƒÂ³s!")
        
        # Volver al boot menu
        import subprocess
        subprocess.Popen(["/usr/bin/python3", "/home/Javo/Proyects/boot_menu/boot_menu.py"])

if __name__ == "__main__":
    player = PracticePlayer()
    player.run()
