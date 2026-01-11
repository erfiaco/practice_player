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
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚ MODE: BROWSER          â”‚
        â”‚ â–º solo_django.wav      â”‚
        â”‚   3/15 files           â”‚
        â”‚ STOP(3s)=Exit          â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # LÃ­nea 1: Modo
        d.text((0, 0), "BROWSER", font=self.font_big, fill=255)
        
        # LÃ­nea 2: Archivo actual con indicador
        # Truncar nombre si es muy largo
        display_name = filename
        if len(filename) > 20:
            display_name = filename[:17] + "..."
        d.text((0, 18), f"> {display_name}", font=self.font_med, fill=255)
        
        # LÃ­nea 3: PosiciÃ³n
        d.text((0, 35), f"  {position}/{total} files", font=self.font_small, fill=255)
        
        # LÃ­nea 4: Ayuda
        d.text((0, 50), help_text, font=self.font_small, fill=255)
        
        self.device.display(img)
    
    def show_player(self, state, current_time, total_time, 
                    point_a=None, point_b=None, tempo=100, 
                    help_text="STOP(3s)=Back"):
        """
        Muestra el modo PLAYER
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚ â–¶ PLAYING [A-B] 85%    â”‚
        â”‚ 00:12.3 / 00:45.8      â”‚
        â”‚ A:00:08.1 B:00:15.7    â”‚
        â”‚ STOP(3s)=Back          â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        
        state: 'PLAYING', 'PAUSED', 'STOPPED'
        times en segundos (float)
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # LÃ­nea 1: Estado + Loop activo + Tempo
        state_icon = "â–¶" if state == "PLAYING" else "â¸" if state == "PAUSED" else "â¹"
        loop_indicator = "[A-B]" if point_a is not None and point_b is not None else ""
        tempo_str = f"{tempo}%" if tempo != 100 else ""
        
        line1 = f"{state_icon} {state} {loop_indicator} {tempo_str}".strip()
        d.text((0, 0), line1, font=self.font_med, fill=255)
        
        # LÃ­nea 2: Tiempo actual / DuraciÃ³n total
        current_str = self._format_time(current_time)
        total_str = self._format_time(total_time)
        d.text((0, 16), f"{current_str} / {total_str}", font=self.font_big, fill=255)
        
        # LÃ­nea 3: Puntos A y B
        if point_a is not None or point_b is not None:
            a_str = f"A:{self._format_time(point_a)}" if point_a is not None else "A:--"
            b_str = f"B:{self._format_time(point_b)}" if point_b is not None else "B:--"
            d.text((0, 36), f"{a_str}  {b_str}", font=self.font_small, fill=255)
        
        # LÃ­nea 4: Ayuda
        d.text((0, 50), help_text, font=self.font_small, fill=255)
        
        self.device.display(img)
    
    def show_adjusting(self, point_name, value):
        """
        Muestra pantalla de ajuste fino
        â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
        â”‚   ADJUSTING POINT A    â”‚
        â”‚                        â”‚
        â”‚    00:08.147           â”‚
        â”‚                        â”‚
        â”‚  â—€ -0.1s    +0.1s â–¶    â”‚
        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        """
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # TÃ­tulo centrado
        if point_name == 'POSITION':
            title = "ADJUSTING POSITION"
        else:
            title = f"ADJUSTING POINT {point_name}"
        d.text((10, 5), title, font=self.font_small, fill=255)
        
        # Valor grande centrado
        time_str = self._format_time(value, show_ms=True)
        d.text((25, 25), time_str, font=self.font_big, fill=255)
        
        # Indicadores de control
        d.text((5, 50), "â—€ -0.1s    +0.1s â–¶", font=self.font_small, fill=255)
        
        self.device.display(img)
    
    def show_processing(self, message="Processing..."):
        """Muestra mensaje de procesamiento (para time-stretch)"""
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        d.text((20, 25), message, font=self.font_big, fill=255)
        
        self.device.display(img)
    
    def show_message(self, message):
        """Muestra un mensaje genÃ©rico centrado"""
        img = Image.new("1", (self.W, self.H))
        d = ImageDraw.Draw(img)
        
        # Dividir en lÃ­neas si es muy largo
        lines = self._wrap_text(message, 21)
        y = 20
        for line in lines[:3]:  # MÃ¡ximo 3 lÃ­neas
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
        """Divide texto en lÃ­neas de max_chars"""
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
