from fastapi import APIRouter, Depends

from app.api.deps import SessionDep, AdminUser
from app.services.maintenance import MaintenanceService
from app.services.backup import BackupService

router = APIRouter()


@router.post("/cleanup", name="run_cleanup_task")
async def run_cleanup_task(
        db: SessionDep,
        admin: AdminUser
):
    """
    Trigger database garbage collection.
    Removes tags, people, and collections that have no associated comics.
    """
    service = MaintenanceService(db)
    stats = service.cleanup_orphans()

    return {
        "message": "Cleanup complete",
        "stats": stats
    }


@router.post("/backup", name="run_backup_task")
async def run_backup_task(
        admin: AdminUser
):
    """
    Trigger a database backup immediately.
    """
    service = BackupService()
    result = service.create_backup()

    return {
        "message": "Backup created successfully",
        "details": result
    }

@router.post("/refresh-descriptions", name="run_refresh_descriptions_task")
async def run_refresh_descriptions_task(
        db: SessionDep,
        admin: AdminUser
):
    """
    Trigger enrichment of reading list descriptions from the seed file.
    """
    service = MaintenanceService(db)
    stats = service.refresh_reading_list_descriptions()

    return {
        "message": "Enrichment complete",
        "stats": stats
    }

@router.post("/refresh-colorscapes", name="run_colorscape_refresh_task")
async def run_colorscape_refresh_task(
        db: SessionDep,
        admin: AdminUser
):
    """
    Generate colors for comics that are missing them.
    """
    service = MaintenanceService(db)
    stats = service.backfill_colors()

    return {
        "message": "ColorScape backfill complete",
        "stats": stats
    }