from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.comic import Comic, Volume
from app.models.series import Series

router = APIRouter()


@router.get("/")
async def list_comics(db: Session = Depends(get_db)):
    """List all comics"""
    comics = db.query(Comic).join(Volume).join(Series).all()

    result = []
    for comic in comics:
        result.append({
            "id": comic.id,
            "filename": comic.filename,
            "series": comic.volume.series.name,
            "volume": comic.volume.volume_number,
            "number": comic.number,
            "title": comic.title,
            "page_count": comic.page_count,
            "year": comic.year
        })

    return {
        "total": len(result),
        "comics": result
    }


@router.get("/{comic_id}")
async def get_comic(comic_id: int, db: Session = Depends(get_db)):
    """Get a specific comic"""
    comic = db.query(Comic).filter(Comic.id == comic_id).first()

    if not comic:
        raise HTTPException(status_code=404, detail="Comic not found")

    return {
        "id": comic.id,
        "filename": comic.filename,
        "file_path": comic.file_path,
        "series": comic.volume.series.name,
        "volume": comic.volume.volume_number,
        "number": comic.number,
        "title": comic.title,
        "summary": comic.summary,
        "page_count": comic.page_count,
        "year": comic.year,
        "writer": comic.writer,
        "alternate_series": comic.alternate_series,
        "alternate_number": comic.alternate_number,
        "story_arc": comic.story_arc,
        "created_at": comic.created_at,
        "updated_at": comic.updated_at
    }