"""
Practice Player - Reproductor para estudiar solos con loop A-B y control de tempo

Módulos:
- file_browser: Navegador de archivos WAV
- audio_player: Engine de reproducción con loop A-B
- tempo_controller: Time-stretching con pyrubberband
- buttons_manager: Gestión de GPIO con tap/hold
- oled_display: Display OLED con layouts específicos
- main: State machine principal
"""

__version__ = "1.0.0"
__author__ = "Javo"

from .file_browser import FileBrowser
from .audio_player import AudioPlayer
from .tempo_controller import TempoController
from .buttons_manager import ButtonsManager
from .oled_display import OledDisplay

__all__ = [
    'FileBrowser',
    'AudioPlayer',
    'TempoController',
    'ButtonsManager',
    'OledDisplay',
]
