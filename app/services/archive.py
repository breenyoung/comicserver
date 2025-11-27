import zipfile
import rarfile
from pathlib import Path
from typing import List, Optional
import io
from app.config import settings
import re

# Import the rarfile configuration
import rarfile
try:
    rarfile.UNRAR_TOOL = settings.unrar_path
except:
    pass

try:
    import py7zr
    CB7_SUPPORT = True
except ImportError:
    CB7_SUPPORT = False
    print("Warning: py7zr not installed. CB7 support disabled.")


class ComicArchive:
    """Unified interface for CBZ, CBR, and CB7 archives"""

    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.extension = filepath.suffix.lower()
        self.archive = self._open_archive()

    def _open_archive(self):
        """Open the appropriate archive handler"""
        if self.extension == ".cbz":
            return zipfile.ZipFile(self.filepath)
        elif self.extension == ".cbr":
            return rarfile.RarFile(self.filepath)
        elif self.extension == ".cb7":
            if not CB7_SUPPORT:
                raise ValueError("CB7 support not available. Install py7zr package.")
            return py7zr.SevenZipFile(self.filepath)
        else:
            raise ValueError(f"Unsupported format: {self.extension}")

    def get_file_list(self) -> List[str]:
        """Get list of files in archive"""
        if self.extension == ".cbz":
            return self.archive.namelist()
        elif self.extension == ".cbr":
            return self.archive.namelist()
        elif self.extension == ".cb7":
            return self.archive.getnames()

    def get_pages(self) -> List[str]:
        """Get sorted list of image files (pages) - filter out non-images"""
        # Valid image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tiff'}

        # Files to explicitly ignore (common in comic archives)
        ignore_patterns = {'thumbs.db', '.ds_store', 'comicinfo.xml', '__macosx'}
        ignore_extensions = {'.nfo', '.sfv', '.txt', '.xml', '.db', '.ini'}

        files = self.get_file_list()

        # Filter to valid images only
        pages = []
        for f in files:
            file_path = Path(f)
            filename_lower = file_path.name.lower()

            # Skip ignored files
            if filename_lower in ignore_patterns:
                continue

            # Skip ignored extensions
            if file_path.suffix.lower() in ignore_extensions:
                continue

            # Only include valid image files
            if file_path.suffix.lower() in image_extensions:
                pages.append(f)

        # --- IMPROVED SORTING LOGIC ---
        def natural_keys(text):
            """
            Sorts strings naturally (1, 2, 10) AND handles the hyphen vs letter issue.

            Logic:
            1. Lowercase everything.
            2. Replace separators (-, _) with a high-ASCII char '~' (ASCII 126).
               This ensures 'a' (97) comes BEFORE '-' (126 in our logic).
               Effect: 'c01a' sorts before 'c01-'
            3. Split into chunks of text and numbers so 'page2' < 'page10'.
            """
            # 1. Normalize case
            text = text.lower()

            # 2. Hack: De-prioritize separators
            # By replacing '-' with '~', we make it sort AFTER letters.
            # 'c01a' -> 'c01a'
            # 'c01-' -> 'c01~'
            # 'a' < '~', so 'c01a' wins.
            text = text.replace('-', '~').replace('_', '~')

            # 3. Split into [text, number, text, number...]
            # 'c01a' -> ['c', 1, 'a']
            return [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', text)]

        # ------------------------------
        pages.sort(key=natural_keys)

        return pages

    def read_file(self, filename: str) -> bytes:
        """Read a specific file from the archive"""
        if self.extension == ".cbz":
            return self.archive.read(filename)
        elif self.extension == ".cbr":
            return self.archive.read(filename)
        elif self.extension == ".cb7":
            return self.archive.read([filename])[filename].read()

    def get_comicinfo(self) -> Optional[bytes]:
        """Extract ComicInfo.xml if it exists"""
        files = self.get_file_list()
        comicinfo = next((f for f in files if f.lower() == "comicinfo.xml"), None)

        if comicinfo:
            return self.read_file(comicinfo)
        return None

    def close(self):
        """Close the archive"""
        self.archive.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()