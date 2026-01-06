import os
import glob

class FileBrowser:
    """Navegador de archivos WAV para seleccionar pistas de estudio"""
    
    def __init__(self, audio_dir="audio_files"):
        self.audio_dir = audio_dir
        self.files = []
        self.current_index = 0
        self._scan_files()
        
    def _scan_files(self):
        """Escanea la carpeta en busca de archivos WAV"""
        # Crear carpeta si no existe
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
            print(f"Carpeta {self.audio_dir} creada. Añade archivos WAV aquí.")
        
        # Buscar archivos WAV
        pattern = os.path.join(self.audio_dir, "*.wav")
        self.files = sorted(glob.glob(pattern))
        
        if not self.files:
            print(f"⚠ No hay archivos WAV en {self.audio_dir}")
        else:
            print(f"✓ {len(self.files)} archivo(s) WAV encontrado(s)")
            
    def refresh(self):
        """Reescanea la carpeta (útil si se añaden archivos en caliente)"""
        old_count = len(self.files)
        self._scan_files()
        if len(self.files) != old_count:
            # Mantener índice válido
            self.current_index = min(self.current_index, len(self.files) - 1)
            
    def next_file(self):
        """Navega al siguiente archivo (circular)"""
        if not self.files:
            return
        self.current_index = (self.current_index + 1) % len(self.files)
        
    def prev_file(self):
        """Navega al archivo anterior (circular)"""
        if not self.files:
            return
        self.current_index = (self.current_index - 1) % len(self.files)
        
    def get_current_file(self):
        """Retorna el path completo del archivo actual"""
        if not self.files:
            return None
        return self.files[self.current_index]
    
    def get_current_filename(self):
        """Retorna solo el nombre del archivo actual (sin path)"""
        filepath = self.get_current_file()
        if filepath:
            return os.path.basename(filepath)
        return "Sin archivos"
    
    def get_file_count(self):
        """Retorna número total de archivos"""
        return len(self.files)
    
    def get_position(self):
        """Retorna (índice_actual + 1, total) para mostrar '3/15'"""
        if not self.files:
            return (0, 0)
        return (self.current_index + 1, len(self.files))
    
    def has_files(self):
        """Retorna True si hay archivos disponibles"""
        return len(self.files) > 0
