from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    app_name: str = "Comic Server"
    database_url: str = "sqlite:///./storage/database/comics.db"

    # Paths
    unrar_path: str = r"C:\Program Files\WinRAR\UnRAR.exe"

    # Storage paths
    cache_dir: Path = Path("./storage/cache")
    cover_dir: Path = Path("./storage/cover")
    #thumbnail_size: tuple = (300, 450)
    thumbnail_size: tuple = (320, 455)

    # Supported formats
    supported_extensions: list = [".cbz", ".cbr"]

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure directories exist
settings.cache_dir.mkdir(parents=True, exist_ok=True)