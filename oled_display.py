from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import threading
import time

class OledDisplay:
    """Display OLED para Practice Player con protección timeout I2C"""
    
    def __init__(self, port=1, address=0x3C, width=128, height=64):
        # Inicializar I2C y device
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)
        self.W, self.H = self.device.size
        
        # Flag para detectar errores I2C
        self.i2c_error_count = 0
        self.i2c_disabled = False
        
        # Fuentes
        try:
            self.font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            self.font_big = ImageFont.load_default()
            self.font_med = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def _safe_display(self, img, timeout=1.0):
        """
        Wrapper seguro para self.device.display() con timeout
        
        Si la operación I2C se bloquea más de timeout segundos:
        - Retorna False
        - Incrementa contador de errores
        - Si hay demasiados errores, deshabilita el display
        """
        if self.i2c_disabled:
            return False
        
        result = {'success': False, 'error': None}
        
        def display_worker():
            try:
                self.device.display(img)
                result['success'] = True
            except Exception as e:
                result['error'] = e
        
        # Ejecutar en thread con timeout
        thread = threading.Thread(target=display_worker, daemon=True)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            # Timeout - el thread sigue bloqueado
            self.i2c_error_count += 1
            print(f"⚠ OLED timeout #{self.i2c_error_count} - I2C no responde")
            
            # Si hay muchos errores consecutivos, deshabilitar display
            if self.i2c_error_count >= 5:
                self.i2c_disabled = True
                print("⚠⚠⚠ OLED deshabilitado - demasiados timeouts I2C")
            
            return False
        
        if result['error']:
            self.i2c_error_count += 1
            print(f"⚠ OLED error: {result['error']}")
            return False
        
        # Operación exitosa - resetear contador
        if result['success']:
            self.i2c_error_count = 0
            return True
        
        return False
    
    def clear(self):
        """Limpia la pantalla"""
        img = Image.new("1", (self.W, self.H))
        self._safe_display(img)
    
    def show_browser(self, filename, position, total, help_text="STOP(3s)=Exit"):
        """
        Muestra el modo BROWSER
        ┌────────────────────────┐
        │ MODE: BROWSER          │
        │ ► solo_django.wav      │
        │   3/15 files           │
        │ STOP(3s)=Exit          │
        └────────────────────────┘
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Línea 1: Modo
        d.text((0, 0), "BROWSER", font=self.font_big, fill=255)
        
        # Línea 2: Nombre de archivo (truncar si es muy largo)
        display_name = filename[:18] if len(filename) > 18 else filename
        d.text((0, 20), f"► {display_name}", font=self.font_med, fill=255)
        
        # Línea 3: Posición
        d.text((0, 36), f"  {position}/{total} files", font=self.font_small, fill=255)
        
        # Línea 4: Ayuda
        d.text((0, 50), help_text, font=self.font_small, fill=255)
        
        self._safe_display(img)
    
    def show_player(self, state, current_time, total_time, point_a=None, point_b=None, 
                    tempo=100, help_text="PLAY A B STOP"):
        """
        Muestra el modo PLAYER
        ┌────────────────────────┐
        │ ▶ PLAYING   100%       │
        │ 00:08.1 / 03:24.5      │
        │ A:01:20  B:02:45       │
        │ PLAY A B STOP          │
        └────────────────────────┘
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Línea 1: Estado y tempo
        state_icon = "▶" if state == "PLAYING" else "⏸" if state == "PAUSED" else "⏹"
        d.text((0, 0), f"{state_icon} {state}", font=self.font_big, fill=255)
        d.text((100, 0), f"{tempo}%", font=self.font_med, fill=255)
        
        # Línea 2: Tiempo
        current_str = self._format_time(current_time)
        total_str = self._format_time(total_time)
        d.text((0, 16), f"{current_str} / {total_str}", font=self.font_big, fill=255)
        
        # Línea 3: Puntos A y B
        if point_a is not None or point_b is not None:
            a_str = f"A:{self._format_time(point_a)}" if point_a is not None else "A:--"
            b_str = f"B:{self._format_time(point_b)}" if point_b is not None else "B:--"
            d.text((0, 36), f"{a_str}  {b_str}", font=self.font_small, fill=255)
        
        # Línea 4: Ayuda
        d.text((0, 50), help_text, font=self.font_small, fill=255)
        
        self._safe_display(img)
    
    def show_adjusting(self, point_name, value):
        """
        Muestra pantalla de ajuste fino
        ┌────────────────────────┐
        │   ADJUSTING POINT A    │
        │                        │
        │    00:08.147           │
        │                        │
        │  ◀ -0.1s    +0.1s ▶    │
        └────────────────────────┘
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Título centrado
        if point_name == 'POSITION':
            title = "ADJUSTING POSITION"
        else:
            title = f"ADJUSTING POINT {point_name}"
        d.text((10, 5), title, font=self.font_small, fill=255)
        
        # Valor grande centrado
        time_str = self._format_time(value, show_ms=True)
        d.text((25, 25), time_str, font=self.font_big, fill=255)
        
        # Indicadores de control
        d.text((5, 50), "◀ -0.1s    +0.1s ▶", font=self.font_small, fill=255)
        
        self._safe_display(img)
    
    def show_processing(self, message="Processing..."):
        """Muestra mensaje de procesamiento (para time-stretch)"""
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        d.text((20, 25), message, font=self.font_big, fill=255)
        
        self._safe_display(img)
    
    def show_message(self, message):
        """Muestra un mensaje genérico centrado"""
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Dividir en líneas si es muy largo
        lines = self._wrap_text(message, 21)
        y = 20
        for line in lines[:3]:  # Máximo 3 líneas
            d.text((5, y), line, font=self.font_med, fill=255)
            y += 15
        
        self._safe_display(img)
    
    def _format_time(self, seconds, show_ms=False):
        """
        Formatea segundos a MM:SS.d o MM:SS.ddd
        Si seconds es None, retorna "--:--"
        """
        if seconds is None:
            return "--:--"
        
        mins = int(seconds // 60)
        secs = seconds % 60
        
        if show_ms:
            return f"{mins:02d}:{secs:06.3f}"
        else:
            return f"{mins:02d}:{secs:04.1f}"
    
    def _wrap_text(self, text, max_chars):
        """Divide texto en líneas de max_chars"""
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_chars:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line:
            lines.append(current_line.strip())
        
        return lines
