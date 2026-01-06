from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

class OledDisplay:
    """Display OLED para Practice Player"""
    
    def __init__(self, port=1, address=0x3C, width=128, height=64):
        # Inicializar I2C y device
        self.serial = i2c(port=port, address=address)
        self.device = ssd1306(self.serial, width=width, height=height)
        self.W, self.H = self.device.size
        
        # Fuentes
        try:
            self.font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
            self.font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
            self.font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 10)
        except:
            self.font_big = ImageFont.load_default()
            self.font_med = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def clear(self):
        """Limpia la pantalla"""
        img = Image.new("1", (self.W, self.H))
        self.device.display(img)
    
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
        
        # Línea 2: Archivo actual con indicador
        # Truncar nombre si es muy largo
        display_name = filename
        if len(filename) > 20:
            display_name = filename[:17] + "..."
        d.text((0, 18), f"> {display_name}", font=self.font_med, fill=255)
        
        # Línea 3: Posición
        d.text((0, 35), f"  {position}/{total} files", font=self.font_small, fill=255)
        
        # Línea 4: Ayuda
        d.text((0, 50), help_text, font=self.font_small, fill=255)
        
        self.device.display(img)
    
    def show_player(self, state, current_time, total_time, 
                    point_a=None, point_b=None, tempo=100, 
                    help_text="STOP(3s)=Back"):
        """
        Muestra el modo PLAYER
        ┌────────────────────────┐
        │ ▶ PLAYING [A-B] 85%    │
        │ 00:12.3 / 00:45.8      │
        │ A:00:08.1 B:00:15.7    │
        │ STOP(3s)=Back          │
        └────────────────────────┘
        
        state: 'PLAYING', 'PAUSED', 'STOPPED'
        times en segundos (float)
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Línea 1: Estado + Loop activo + Tempo
        state_icon = "▶" if state == "PLAYING" else "⏸" if state == "PAUSED" else "⏹"
        loop_indicator = "[A-B]" if point_a is not None and point_b is not None else ""
        tempo_str = f"{tempo}%" if tempo != 100 else ""
        
        line1 = f"{state_icon} {state} {loop_indicator} {tempo_str}".strip()
        d.text((0, 0), line1, font=self.font_med, fill=255)
        
        # Línea 2: Tiempo actual / Duración total
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
        
        self.device.display(img)
    
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
        title = f"ADJUSTING POINT {point_name}"
        d.text((10, 5), title, font=self.font_small, fill=255)
        
        # Valor grande centrado
        time_str = self._format_time(value, show_ms=True)
        d.text((25, 25), time_str, font=self.font_big, fill=255)
        
        # Indicadores de control
        d.text((5, 50), "◀ -0.1s    +0.1s ▶", font=self.font_small, fill=255)
        
        self.device.display(img)
    
    def show_processing(self, message="Processing..."):
        """Muestra mensaje de procesamiento (para time-stretch)"""
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        d.text((20, 25), message, font=self.font_big, fill=255)
        
        self.device.display(img)
    
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
        
        self.device.display(img)
    
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
