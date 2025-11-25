from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from app.database import get_db
from app.models.comic import Comic, Volume
from app.models.series import Series
from app.models.collection import Collection, CollectionItem
from app.models.reading_list import ReadingList, ReadingListItem

router = APIRouter()


@router.get("/{series_id}")
async def get_series_detail(series_id: int, db: Session = Depends(get_db)):
    """Get comprehensive series details including all issues, metadata, and related content"""
    
    # Get series
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Get all volumes for this series
    volumes = db.query(Volume).filter(Volume.series_id == series_id).all()
    
    # Get all comics for this series (through volumes)
    volume_ids = [v.id for v in volumes]
    comics = db.query(Comic).filter(Comic.volume_id.in_(volume_ids)).all()
    
    # Process issues data
    issues_data = []
    for comic in comics:
        issues_data.append({
            "id": comic.id,
            "volume_number": comic.volume.volume_number,
            "number": comic.number,
            "title": comic.title,
            "year": comic.year,
            "format": comic.format,
            "filename": comic.filename
        })
    
    # Count statistics
    annuals = [c for c in comics if c.format and c.format.lower() == 'annual']
    specials = [c for c in comics if c.format and c.format.lower() != 'annual' and c.format]
    
    # Get first issue (earliest by volume then issue number)
    first_issue = None
    if comics:
        sorted_comics = sorted(comics, key=lambda c: (c.volume.volume_number, float(c.number) if c.number else 0))
        first_issue = sorted_comics[0] if sorted_comics else None
    
    # Get related collections (collections that contain any issue from this series)
    related_collections = []
    collection_items = db.query(CollectionItem).filter(
        CollectionItem.comic_id.in_([c.id for c in comics])
    ).all()
    
    collection_ids = list(set([item.collection_id for item in collection_items]))
    if collection_ids:
        collections = db.query(Collection).filter(Collection.id.in_(collection_ids)).all()
        for col in collections:
            related_collections.append({
                "id": col.id,
                "name": col.name,
                "description": col.description,
                "comic_count": len(col.items)
            })
    
    # Get related reading lists
    related_reading_lists = []
    reading_list_items = db.query(ReadingListItem).filter(
        ReadingListItem.comic_id.in_([c.id for c in comics])
    ).all()
    
    reading_list_ids = list(set([item.reading_list_id for item in reading_list_items]))
    if reading_list_ids:
        reading_lists = db.query(ReadingList).filter(ReadingList.id.in_(reading_list_ids)).all()
        for rl in reading_lists:
            related_reading_lists.append({
                "id": rl.id,
                "name": rl.name,
                "description": rl.description,
                "comic_count": len(rl.items)
            })
    
    # Aggregate details across all issues
    writers = set()
    pencillers = set()
    characters = set()
    teams = set()
    locations = set()
    
    for comic in comics:
        # Credits
        for credit in comic.credits:
            if credit.role == 'writer':
                writers.add(credit.person.name)
            elif credit.role == 'penciller':
                pencillers.add(credit.person.name)
        
        # Tags
        for char in comic.characters:
            characters.add(char.name)
        for team in comic.teams:
            teams.add(team.name)
        for loc in comic.locations:
            locations.add(loc.name)
    
    # Get folder path (from first volume if available)
    folder_path = None
    if volumes:
        # Assuming volumes might have a path or we derive from first comic
        if comics:
            first_comic_path = comics[0].file_path
            if first_comic_path:
                # Get directory of first comic
                from pathlib import Path
                folder_path = str(Path(first_comic_path).parent)
    
    return {
        "id": series.id,
        "name": series.name,
        "publisher": comics[0].publisher if comics else None,
        "start_year": first_issue.year if first_issue else None,
        "volume_count": len(volumes),
        "total_issues": len(comics),
        "annual_count": len(annuals),
        "special_count": len(specials),
        "folder_path": folder_path,
        "issues": issues_data,
        "collections": related_collections,
        "reading_lists": related_reading_lists,
        "details": {
            "writers": sorted(list(writers)),
            "pencillers": sorted(list(pencillers)),
            "characters": sorted(list(characters)),
            "teams": sorted(list(teams)),
            "locations": sorted(list(locations))
        }
    }
