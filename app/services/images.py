from pathlib import Path
from typing import Optional, List
from io import BytesIO
from PIL import Image
import hashlib

from app.services.archive import ComicArchive
from app.config import settings


class ImageService:
    """Service for extracting and serving images from comic archives"""

    def __init__(self):
        self.cache_dir = settings.cache_dir
        self.thumbnail_size = settings.thumbnail_size

    def get_page_image(self, comic_path: str, page_index: int) -> Optional[bytes]:
        """
        Extract a specific page from a comic archive

        Args:
            comic_path: Path to the comic file
            page_index: Zero-based page index

        Returns:
            Image bytes or None if page not found
        """
        try:
            file_path = Path(comic_path)

            if not file_path.exists():
                print(f"Comic file not found: {comic_path}")
                return None

            with ComicArchive(file_path) as archive:
                pages = archive.get_pages()

                if page_index < 0 or page_index >= len(pages):
                    print(f"Page index {page_index} out of range (0-{len(pages) - 1})")
                    return None

                page_filename = pages[page_index]
                image_bytes = archive.read_file(page_filename)

                return image_bytes

        except Exception as e:
            print(f"Error extracting page {page_index} from {comic_path}: {e}")
            return None

    def get_cover_image(self, comic_path: str) -> Optional[bytes]:
        """Get the first page (cover) of a comic"""
        return self.get_page_image(comic_path, 0)

    def get_page_count(self, comic_path: str) -> int:
        """Get the number of pages in a comic"""
        try:
            file_path = Path(comic_path)

            if not file_path.exists():
                return 0

            with ComicArchive(file_path) as archive:
                pages = archive.get_pages()
                return len(pages)

        except Exception as e:
            print(f"Error getting page count from {comic_path}: {e}")
            return 0

    def get_thumbnail(self, comic_path: str, width: int = None, height: int = None) -> Optional[bytes]:
        """
        Get or generate a thumbnail for a comic cover

        Args:
            comic_path: Path to the comic file
            width: Thumbnail width (default from config)
            height: Thumbnail height (default from config)

        Returns:
            WebP thumbnail bytes or None
        """
        if width is None or height is None:
            width, height = self.thumbnail_size

        # Generate cache key based on file path and size
        cache_key = hashlib.md5(f"{comic_path}_{width}_{height}".encode()).hexdigest()
        cache_file = self.cache_dir / f"{cache_key}.webp"

        # Check if cached thumbnail exists
        if cache_file.exists():
            try:
                return cache_file.read_bytes()
            except Exception as e:
                print(f"Error reading cached thumbnail: {e}")

        # Generate new thumbnail
        cover_bytes = self.get_cover_image(comic_path)
        if not cover_bytes:
            return None

        try:
            # Open image and create thumbnail
            img = Image.open(BytesIO(cover_bytes))

            # Convert to RGB if necessary (for WebP compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            # Create thumbnail (maintains aspect ratio)
            img.thumbnail((width, height), Image.Resampling.LANCZOS)

            # Save as WebP
            output = BytesIO()
            img.save(output, format='WEBP', quality=85, method=6)
            thumbnail_bytes = output.getvalue()

            # Cache the thumbnail
            try:
                cache_file.write_bytes(thumbnail_bytes)
            except Exception as e:
                print(f"Error caching thumbnail: {e}")

            return thumbnail_bytes

        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return None

    def clear_thumbnail_cache(self, comic_path: str = None):
        """
        Clear thumbnail cache

        Args:
            comic_path: Specific comic to clear, or None to clear all
        """
        if comic_path:
            # Clear specific comic's thumbnails
            cache_pattern = hashlib.md5(comic_path.encode()).hexdigest()[:8]
            for cache_file in self.cache_dir.glob(f"{cache_pattern}*.webp"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    print(f"Error deleting cache file {cache_file}: {e}")
        else:
            # Clear all thumbnails
            for cache_file in self.cache_dir.glob("*.webp"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    print(f"Error deleting cache file {cache_file}: {e}")