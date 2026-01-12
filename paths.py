import os

FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "audio_files")

def get_loop_path(nombre):
    """Genera path completo para un loop."""
    if not os.path.exists(FILES_DIR):
        os.makedirs(FILES_DIR)
    return os.path.join(FILES_DIR, nombre)
