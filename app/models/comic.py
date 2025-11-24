from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Volume(Base):
    __tablename__ = "volumes"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(Integer, ForeignKey("series.id"))
    volume_number = Column(Integer, default=1)

    series = relationship("Series", back_populates="volumes")
    comics = relationship("Comic", back_populates="volume", cascade="all, delete-orphan")


class Comic(Base):
    __tablename__ = "comics"

    id = Column(Integer, primary_key=True, index=True)
    volume_id = Column(Integer, ForeignKey("volumes.id"))

    filename = Column(String, nullable=False)
    file_path = Column(String, unique=True, nullable=False)
    file_modified_at = Column(Float)  # Store as timestamp for easy comparison
    page_count = Column(Integer, default=0)

    # Metadata from ComicInfo.xml
    number = Column(String)
    title = Column(String)
    summary = Column(Text)
    year = Column(Integer)
    writer = Column(String)

    # Reading list support
    alternate_series = Column(String)
    alternate_number = Column(String)
    story_arc = Column(String)

    # Full metadata JSON
    metadata_json = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    volume = relationship("Volume", back_populates="comics")