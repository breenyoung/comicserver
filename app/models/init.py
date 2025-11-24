# Import all models here so SQLAlchemy can set up relationships
from app.models.library import Library
from app.models.series import Series
from app.models.comic import Volume, Comic  # Both Volume and Comic are in comic.py

# This ensures all models are loaded before relationships are configured
__all__ = ['Library', 'Series', 'Volume', 'Comic']

# Import other models here as we create them