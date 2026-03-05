import os
import glob

class FileBrowser:
    def __init__(self, audio_dir="audio_files"):
        self.audio_dir = os.path.abspath(audio_dir)
        self.current_dir = self.audio_dir
        self.items = []        # Lista de lo que se muestra (mix de carpetas, ..., y wavs)
        self.current_index = 0
        
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)
        
        self._scan()

    def _scan(self):
        """Escanea el directorio actual y construye la lista de ítems"""
        self.items = []
        self.current_index = 0

        # Si no estamos en la raíz, añadir ".." para subir
        if self.current_dir != self.audio_dir:
            self.items.append(('up', '...'))

        # Carpetas primero (ordenadas por nombre)
        dirs = sorted([
            d for d in os.listdir(self.current_dir)
            if os.path.isdir(os.path.join(self.current_dir, d))
            and not d.startswith('.')
        ])
        for d in dirs:
            self.items.append(('dir', d))

        # Luego archivos WAV (ordenados por fecha, más reciente primero)
        wavs = glob.glob(os.path.join(self.current_dir, "*.wav"))
        wavs = sorted(wavs, key=os.path.getmtime, reverse=True)
        for w in wavs:
            self.items.append(('wav', os.path.basename(w)))

        if not self.items:
            print(f"⚠ Carpeta vacía: {self.current_dir}")
        else:
            print(f"✓ {len(self.items)} ítem(s) en {self._relative_path()}")

    def _relative_path(self):
        """Devuelve el path relativo a audio_dir para mostrar en OLED"""
        rel = os.path.relpath(self.current_dir, self.audio_dir)
        if rel == '.':
            return '/'
        return '/' + rel + '/'

    def next_file(self):
        if not self.items:
            return
        self.current_index = (self.current_index + 1) % len(self.items)

    def prev_file(self):
        if not self.items:
            return
        self.current_index = (self.current_index - 1) % len(self.items)

    def select(self):
        """
        Ejecuta la acción del ítem actual.
        Devuelve:
          ('wav', path_completo)   → cargar archivo
          ('entered', None)        → entró en carpeta (ya hizo _scan)
          ('up', None)             → subió un nivel (ya hizo _scan)
          (None, None)             → no hay ítems
        """
        if not self.items:
            return (None, None)

        kind, name = self.items[self.current_index]

        if kind == 'wav':
            return ('wav', os.path.join(self.current_dir, name))

        elif kind == 'dir':
            self.current_dir = os.path.join(self.current_dir, name)
            self._scan()
            return ('entered', None)

        elif kind == 'up':
            self.current_dir = os.path.dirname(self.current_dir)
            self._scan()
            return ('up', None)

        return (None, None)

    def refresh(self):
        self._scan()

    # ---- Getters para la UI ----

    def get_current_item_name(self):
        """Nombre del ítem actual para mostrar en OLED"""
        if not self.items:
            return "Sin archivos"
        kind, name = self.items[self.current_index]
        if kind == 'dir':
            return name + '/'
        return name

    def get_current_item_kind(self):
        """Tipo del ítem actual: 'wav', 'dir', 'up' o None"""
        if not self.items:
            return None
        return self.items[self.current_index][0]

    def get_position(self):
        if not self.items:
            return (0, 0)
        return (self.current_index + 1, len(self.items))

    def get_current_dir_label(self):
        """Etiqueta corta del directorio actual para cabecera OLED"""
        return self._relative_path()

    def has_files(self):
        return any(kind == 'wav' for kind, _ in self.items)

    def has_items(self):
        return len(self.items) > 0

    # Compatibilidad con código existente
    def get_current_file(self):
        if not self.items:
            return None
        kind, name = self.items[self.current_index]
        if kind == 'wav':
            return os.path.join(self.current_dir, name)
        return None

    def get_current_filename(self):
        return self.get_current_item_name()

    def get_file_count(self):
        return len(self.items)
