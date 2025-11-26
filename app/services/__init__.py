import rarfile
from app.config import settings

# Use the path defined in config.py
if settings.unrar_path:
    rarfile.UNRAR_TOOL = settings.unrar_path