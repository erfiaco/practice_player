import numpy as np
import scipy.io.wavfile as wav
import datetime
import os
from paths import paths

class AudioClip:
    SAMPLE_RATE = 44100
    CHANNELS = 2

    def __init__(self, datos=None, nombre=None, SAMPLE_RATE=44100):
        self.datos = datos  # Numpy array de audio
        self.nombre = nombre or f"loop_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        self.path = paths.get_loop_path(self.nombre)
        self.duracion = len(self.datos) / self.SAMPLE_RATE if self.datos is not None else 0

    def guardar(self):
        """Guarda a WAV."""
        if self.datos is not None:
            wav.write(self.path, self.SAMPLE_RATE, self.datos.astype(np.float32))
            self.duracion = len(self.datos) / self.SAMPLE_RATE
            return self.path
        return None

    def info(self):
        """String con info del clip."""
        return f"{self.nombre}: {self.duracion:.2f}s"

    @classmethod
    def cargar(cls, path):
        """Carga desde archivo (estático)."""
        sample_rate, data = wav.read(path)
        return cls(data, os.path.basename(path))
