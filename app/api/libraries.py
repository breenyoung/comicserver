from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.library import Library
from app.services.scanner import LibraryScanner

router = APIRouter()


@router.get("/")
async def list_libraries(db: Session = Depends(get_db)):
    """List all libraries"""
    libraries = db.query(Library).all()
    return libraries


@router.post("/")
async def create_library(name: str, path: str, db: Session = Depends(get_db)):
    """Create a new library"""
    library = Library(name=name, path=path)
    db.add(library)
    db.commit()
    db.refresh(library)
    return library


@router.get("/{library_id}")
async def get_library(library_id: int, db: Session = Depends(get_db)):
    """Get a specific library"""
    library = db.query(Library).filter(Library.id == library_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")
    return library


@router.delete("/{library_id}")
async def delete_library(library_id: int, db: Session = Depends(get_db)):
    """Delete a library"""
    library = db.query(Library).filter(Library.id == library_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")

    db.delete(library)
    db.commit()
    return {"message": "Library deleted"}


@router.post("/{library_id}/scan")
async def scan_library(library_id: int, db: Session = Depends(get_db)):
    """Scan a library for comics and import them"""
    library = db.query(Library).filter(Library.id == library_id).first()
    if not library:
        raise HTTPException(status_code=404, detail="Library not found")

    scanner = LibraryScanner(library, db)
    results = scanner.scan()

    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    return results