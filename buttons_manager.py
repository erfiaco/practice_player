from gpiozero import Button, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time
import threading

Device.pin_factory = LGPIOFactory()

class ButtonsManager:
    """
    Gestor de botones para Practice Player
    Soporta TAP y HOLD para diferentes funciones
    """
    
    def __init__(self):
        # Inicializar botones con pull_up
        self.btn_play     = Button(6,  pull_up=True, bounce_time=0.03, hold_time=3.0)
        self.btn_mark_a   = Button(26, pull_up=True, bounce_time=0.03, hold_time=1.0)
        self.btn_mark_b   = Button(13,  pull_up=True, bounce_time=0.03, hold_time=1.0)
        self.btn_stop     = Button(5, pull_up=True, bounce_time=0.03, hold_time=3.0)
        self.btn_tempo_dn = Button(9, pull_up=True, bounce_time=0.03, hold_time=0.3)
        self.btn_tempo_up = Button(22, pull_up=True, bounce_time=0.03, hold_time=0.3)
        self.btn_save_loop = Button(25, pull_up=True, bounce_time=0.03, hold_time=1.0)
        
        # Callbacks vacÃƒÂ­os por defecto
        self._callbacks = {
            'play': None,
            'play_hold': None,
            'mark_a_tap': None,
            'mark_a_hold': None,
            'mark_b_tap': None,
            'mark_b_hold': None,
            'stop_tap': None,
            'stop_hold': None,
            'tempo_down': None,
            'tempo_up': None,
            'save_loop': None,
        }
        
        # Estado para detectar tap vs hold
        self._play_held = False
        self._mark_a_held = False
        self._mark_b_held = False
        
        # Estado para botones de tempo (ajuste progresivo)
        self._tempo_down_held = False
        self._tempo_up_held = False
        self._tempo_hold_start_time = None
        self._tempo_repeat_thread = None
        
        # Asignar handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Configura los event handlers de los botones"""
        # Play/Pause - tap vs hold
        self.btn_play.when_pressed = self._on_play_press
        self.btn_play.when_held = self._on_play_held
        self.btn_play.when_released = self._on_play_release
        
        # Mark A - tap vs hold
        self.btn_mark_a.when_pressed = self._on_mark_a_press
        self.btn_mark_a.when_held = self._on_mark_a_held
        self.btn_mark_a.when_released = self._on_mark_a_release
        
        # Mark B - tap vs hold
        self.btn_mark_b.when_pressed = self._on_mark_b_press
        self.btn_mark_b.when_held = self._on_mark_b_held
        self.btn_mark_b.when_released = self._on_mark_b_release
        
        # Stop - tap (normal) vs hold (3s)
        self.btn_stop.when_pressed = self._on_stop_tap
        self.btn_stop.when_held = self._on_stop_hold
        
        # Tempo - con repeticiÃƒÂ³n progresiva
        self.btn_tempo_dn.when_pressed = self._on_tempo_down_press
        self.btn_tempo_dn.when_released = self._on_tempo_down_release
        
        self.btn_tempo_up.when_pressed = self._on_tempo_up_press
        self.btn_tempo_up.when_released = self._on_tempo_up_release
        
        # Save Loop
        self.btn_save_loop.when_pressed = self._on_save_loop
        
    # === Play (tap vs hold) ===
    def _on_play_press(self):
        self._play_held = False
        
    def _on_play_held(self):
        self._play_held = True
        if self._callbacks['play_hold']:
            self._callbacks['play_hold']()
    
    def _on_play_release(self):
        # Si no se activÃƒÂ³ hold, es un tap
        if not self._play_held:
            if self._callbacks['play']:
                self._callbacks['play']()
        self._play_held = False
    
    # === Mark A (tap vs hold) ===
    def _on_mark_a_press(self):
        self._mark_a_held = False
        
    def _on_mark_a_held(self):
        self._mark_a_held = True
        if self._callbacks['mark_a_hold']:
            self._callbacks['mark_a_hold']()
    
    def _on_mark_a_release(self):
        # Si no se activÃƒÂ³ hold, es un tap
        if not self._mark_a_held:
            if self._callbacks['mark_a_tap']:
                self._callbacks['mark_a_tap']()
        self._mark_a_held = False
    
    # === Mark B (tap vs hold) ===
    def _on_mark_b_press(self):
        self._mark_b_held = False
        
    def _on_mark_b_held(self):
        self._mark_b_held = True
        if self._callbacks['mark_b_hold']:
            self._callbacks['mark_b_hold']()
    
    def _on_mark_b_release(self):
        # Si no se activÃƒÂ³ hold, es un tap
        if not self._mark_b_held:
            if self._callbacks['mark_b_tap']:
                self._callbacks['mark_b_tap']()
        self._mark_b_held = False
    
    # === Stop (tap vs hold) ===
    def _on_stop_tap(self):
        if self._callbacks['stop_tap']:
            self._callbacks['stop_tap']()
    
    def _on_stop_hold(self):
        if self._callbacks['stop_hold']:
            self._callbacks['stop_hold']()
    
    # === Tempo (con repeticiÃƒÂ³n progresiva) ===
    def _on_tempo_down_press(self):
        """Inicia ajuste hacia abajo con repeticiÃƒÂ³n progresiva"""
        self._tempo_down_held = True
        self._tempo_hold_start_time = time.time()
        
        # Primera llamada inmediata
        if self._callbacks['tempo_down']:
            self._callbacks['tempo_down'](0.1)  # Primera pulsaciÃƒÂ³n: 0.1s
        
        # Iniciar thread de repeticiÃƒÂ³n
        if self._tempo_repeat_thread is None or not self._tempo_repeat_thread.is_alive():
            self._tempo_repeat_thread = threading.Thread(
                target=self._tempo_repeat_worker, 
                args=('down',),
                daemon=True
            )
            self._tempo_repeat_thread.start()
    
    def _on_tempo_down_release(self):
        """Detiene el ajuste hacia abajo"""
        self._tempo_down_held = False
    
    def _on_tempo_up_press(self):
        """Inicia ajuste hacia arriba con repeticiÃƒÂ³n progresiva"""
        self._tempo_up_held = True
        self._tempo_hold_start_time = time.time()
        
        # Primera llamada inmediata
        if self._callbacks['tempo_up']:
            self._callbacks['tempo_up'](0.1)  # Primera pulsaciÃƒÂ³n: 0.1s
        
        # Iniciar thread de repeticiÃƒÂ³n
        if self._tempo_repeat_thread is None or not self._tempo_repeat_thread.is_alive():
            self._tempo_repeat_thread = threading.Thread(
                target=self._tempo_repeat_worker, 
                args=('up',),
                daemon=True
            )
            self._tempo_repeat_thread.start()
    
    def _on_tempo_up_release(self):
        """Detiene el ajuste hacia arriba"""
        self._tempo_up_held = False
    
    def _tempo_repeat_worker(self, direction):
        """
        Worker thread que repite el ajuste mientras el botÃƒÂ³n estÃƒÂ© pulsado
        Delta progresivo:
        - 0-1s: 0.1s por pulsaciÃƒÂ³n (ajuste fino)
        - 1-2s: 0.5s por pulsaciÃƒÂ³n (ajuste medio)
        - >2s: 1.0s por pulsaciÃƒÂ³n (ajuste rÃƒÂ¡pido)
        """
        time.sleep(0.3)  # Delay inicial antes de empezar a repetir
        
        callback = self._callbacks['tempo_down'] if direction == 'down' else self._callbacks['tempo_up']
        is_held = lambda: self._tempo_down_held if direction == 'down' else self._tempo_up_held
        
        if not callback:
            return
        
        while is_held():
            # Calcular tiempo transcurrido desde que se pulsÃƒÂ³
            elapsed = time.time() - self._tempo_hold_start_time
            
            # Determinar delta segÃƒÂºn tiempo transcurrido
            if elapsed < 1.0:
                delta = 0.1
                repeat_delay = 0.15  # Repetir cada 150ms
            elif elapsed < 2.0:
                delta = 0.5
                repeat_delay = 0.12  # Repetir cada 120ms (mÃƒÂ¡s rÃƒÂ¡pido)
            else:
                delta = 1.0
                repeat_delay = 0.10  # Repetir cada 100ms (aÃƒÂºn mÃƒÂ¡s rÃƒÂ¡pido)
            
            # Llamar al callback con el delta apropiado
            callback(delta)
            
            # Esperar antes de la siguiente repeticiÃƒÂ³n
            time.sleep(repeat_delay)
    
    # === Save Loop ===
    def _on_save_loop(self):
        """Guarda la secciÃƒÂ³n A-B como nuevo archivo"""
        if self._callbacks['save_loop']:
            self._callbacks['save_loop']()
    
    # === API pÃƒÂºblica para asignar callbacks ===
    def set_callback(self, event, callback):
        """
        Asigna un callback a un evento especÃƒÂ­fico
        Eventos vÃƒÂ¡lidos:
        - 'play', 'play_hold'
        - 'mark_a_tap', 'mark_a_hold'
        - 'mark_b_tap', 'mark_b_hold'
        - 'stop_tap', 'stop_hold'
        - 'tempo_down', 'tempo_up'
        """
        if event in self._callbacks:
            self._callbacks[event] = callback
        else:
            raise ValueError(f"Evento desconocido: {event}")
    
    def set_browser_mode(self, on_prev, on_next, on_select, on_exit):
        """
        Configura callbacks para modo BROWSER
        - GPIO23 (tempo_dn) Ã¢â€ â€™ Archivo anterior
        - GPIO22 (tempo_up) Ã¢â€ â€™ Archivo siguiente
        - GPIO5 TAP Ã¢â€ â€™ Seleccionar
        - GPIO13 HOLD Ã¢â€ â€™ Salir
        """
        self.set_callback('tempo_down', on_prev)
        self.set_callback('tempo_up', on_next)
        self.set_callback('play', on_select)
        self.set_callback('stop_hold', on_exit)
    
    def set_player_mode(self, on_play, on_play_hold, on_mark_a_tap, on_mark_a_hold,
                        on_mark_b_tap, on_mark_b_hold, on_stop, on_back,
                        on_tempo_down, on_tempo_up, on_save_loop):
        """
        Configura callbacks para modo PLAYER
        """
        self.set_callback('play', on_play)
        self.set_callback('play_hold', on_play_hold)
        self.set_callback('mark_a_tap', on_mark_a_tap)
        self.set_callback('mark_a_hold', on_mark_a_hold)
        self.set_callback('mark_b_tap', on_mark_b_tap)
        self.set_callback('mark_b_hold', on_mark_b_hold)
        self.set_callback('stop_tap', on_stop)
        self.set_callback('stop_hold', on_back)
        self.set_callback('tempo_down', on_tempo_down)
        self.set_callback('tempo_up', on_tempo_up)
        self.set_callback('save_loop', on_save_loop)
    
    def close(self):
        """Libera recursos GPIO"""
        try:
            self.btn_play.close()
            self.btn_mark_a.close()
            self.btn_mark_b.close()
            self.btn_stop.close()
            self.btn_tempo_dn.close()
            self.btn_tempo_up.close()
            self.btn_save_loop.close()
        except:
            pass
