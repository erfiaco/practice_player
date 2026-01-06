from gpiozero import Button, Device
from gpiozero.pins.lgpio import LGPIOFactory
import time

Device.pin_factory = LGPIOFactory()

class ButtonsManager:
    """
    Gestor de botones para Practice Player
    Soporta TAP y HOLD para diferentes funciones
    """
    
    def __init__(self):
        # Inicializar botones con pull_up
        self.btn_play     = Button(5,  pull_up=True, bounce_time=0.03)
        self.btn_mark_a   = Button(26, pull_up=True, bounce_time=0.03, hold_time=1.0)
        self.btn_mark_b   = Button(6,  pull_up=True, bounce_time=0.03, hold_time=1.0)
        self.btn_stop     = Button(13, pull_up=True, bounce_time=0.03, hold_time=3.0)
        self.btn_tempo_dn = Button(23, pull_up=True, bounce_time=0.03)
        self.btn_tempo_up = Button(22, pull_up=True, bounce_time=0.03)
        
        # Callbacks vacíos por defecto
        self._callbacks = {
            'play': None,
            'mark_a_tap': None,
            'mark_a_hold': None,
            'mark_b_tap': None,
            'mark_b_hold': None,
            'stop_tap': None,
            'stop_hold': None,
            'tempo_down': None,
            'tempo_up': None,
        }
        
        # Estado para detectar tap vs hold
        self._mark_a_held = False
        self._mark_b_held = False
        
        # Asignar handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Configura los event handlers de los botones"""
        # Play/Pause - simple
        self.btn_play.when_pressed = self._on_play
        
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
        
        # Tempo - simples (pueden repetir si se mantienen)
        self.btn_tempo_dn.when_pressed = self._on_tempo_down
        self.btn_tempo_up.when_pressed = self._on_tempo_up
        
    # === Play ===
    def _on_play(self):
        if self._callbacks['play']:
            self._callbacks['play']()
    
    # === Mark A (tap vs hold) ===
    def _on_mark_a_press(self):
        self._mark_a_held = False
        
    def _on_mark_a_held(self):
        self._mark_a_held = True
        if self._callbacks['mark_a_hold']:
            self._callbacks['mark_a_hold']()
    
    def _on_mark_a_release(self):
        # Si no se activó hold, es un tap
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
        # Si no se activó hold, es un tap
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
    
    # === Tempo ===
    def _on_tempo_down(self):
        if self._callbacks['tempo_down']:
            self._callbacks['tempo_down']()
    
    def _on_tempo_up(self):
        if self._callbacks['tempo_up']:
            self._callbacks['tempo_up']()
    
    # === API pública para asignar callbacks ===
    def set_callback(self, event, callback):
        """
        Asigna un callback a un evento específico
        Eventos válidos:
        - 'play'
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
        - GPIO23 (tempo_dn) → Archivo anterior
        - GPIO22 (tempo_up) → Archivo siguiente
        - GPIO13 TAP → Seleccionar
        - GPIO13 HOLD → Salir
        """
        self.set_callback('tempo_down', on_prev)
        self.set_callback('tempo_up', on_next)
        self.set_callback('stop_tap', on_select)
        self.set_callback('stop_hold', on_exit)
    
    def set_player_mode(self, on_play, on_mark_a_tap, on_mark_a_hold,
                        on_mark_b_tap, on_mark_b_hold, on_stop, on_back,
                        on_tempo_down, on_tempo_up):
        """
        Configura callbacks para modo PLAYER
        """
        self.set_callback('play', on_play)
        self.set_callback('mark_a_tap', on_mark_a_tap)
        self.set_callback('mark_a_hold', on_mark_a_hold)
        self.set_callback('mark_b_tap', on_mark_b_tap)
        self.set_callback('mark_b_hold', on_mark_b_hold)
        self.set_callback('stop_tap', on_stop)
        self.set_callback('stop_hold', on_back)
        self.set_callback('tempo_down', on_tempo_down)
        self.set_callback('tempo_up', on_tempo_up)
    
    def close(self):
        """Libera recursos GPIO"""
        try:
            self.btn_play.close()
            self.btn_mark_a.close()
            self.btn_mark_b.close()
            self.btn_stop.close()
            self.btn_tempo_dn.close()
            self.btn_tempo_up.close()
        except:
            pass
