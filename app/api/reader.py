from fastapi import APIRouter

router = APIRouter()

@router.get("/{comic_id}")
async def read_comic(comic_id: int):
    """Comic reader view"""
    return {"message": f"Reader for comic {comic_id} - coming soon"}

@router.get("/{comic_id}/page/{page_num}")
async def get_page(comic_id: int, page_num: int):
    """Get a specific page from a comic"""
    return {"message": f"Comic {comic_id}, page {page_num} - coming soon"}