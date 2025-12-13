import threading
import time
import json
import traceback
import logging
from datetime import datetime, timezone
from sqlalchemy import asc

from app.core.settings_loader import get_cached_setting
from app.database import SessionLocal
from app.models import ScanJob, Library
from app.models.job import JobType, JobStatus

from app.services.scanner import LibraryScanner
from app.services.maintenance import MaintenanceService
from app.services.thumbnailer import ThumbnailService


class ScanManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ScanManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.logger = logging.getLogger(__name__)

        self._stop_event = threading.Event()

        # 1. RECOVERY: Check for jobs interrupted by a crash
        self._recover_interrupted_jobs()

        # 2. Start the DB polling worker
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

        self._initialized = True

    def _recover_interrupted_jobs(self):
        """Mark jobs that were 'RUNNING' during startup as FAILED"""
        db = SessionLocal()
        try:
            stuck_jobs = db.query(ScanJob).filter(ScanJob.status == JobStatus.RUNNING).all()
            if stuck_jobs:
                self.logger.info(f"Recovering {len(stuck_jobs)} interrupted scan jobs...")

                for job in stuck_jobs:
                    job.status = JobStatus.FAILED
                    job.error_message = "Scan interrupted by server restart"
                    job.completed_at = datetime.now(timezone.utc)
                    # Reset library flag directly here
                    if job.library:
                        job.library.is_scanning = False
                db.commit()
        except Exception as e:
            self.logger.error(f"Error during job recovery: {e}")
        finally:
            db.close()

    def _set_library_scanning_status(self, library_id: int, is_scanning: bool):
        """
        Helper: Update library status in a fresh, isolated transaction.
        Includes retry logic to handle SQLite locking gracefully.
        """
        if not library_id:
            return

        # Try up to 3 times to grab the lock
        for attempt in range(3):
            db = SessionLocal()
            try:
                # We use a direct UPDATE statement for speed and atomicity
                db.query(Library).filter(Library.id == library_id).update(
                    {"is_scanning": is_scanning}
                )
                db.commit()
                return  # Success
            except Exception as e:
                # If locked, wait a split second and retry
                if "locked" in str(e).lower() and attempt < 2:
                    time.sleep(0.5)
                    continue
                self.logger.error(f"Failed to set library {library_id} scanning={is_scanning}: {e}")
            finally:
                db.close()

    def add_task(self, library_id: int, force: bool = False) -> dict:
        """Create a new job record"""
        db = SessionLocal()
        try:
            # STRICT BLOCKING: Do not allow queuing if a scan is already active/pending
            existing = db.query(ScanJob).filter(
                ScanJob.library_id == library_id,
                ScanJob.job_type == JobType.SCAN,
                ScanJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            ).first()

            if existing:
                return {
                    "status": "ignored",
                    "job_id": existing.id,
                    "message": f"Scan already exists in state: {existing.status}"
                }

            job = ScanJob(
                library_id=library_id,
                force_scan=force,
                job_type=JobType.SCAN,
                status=JobStatus.PENDING
            )
            db.add(job)
            db.commit()
            db.refresh(job)

            return {
                "status": "queued",
                "job_id": job.id,
                "message": "Scan job queued"
            }
        finally:
            db.close()

    def _process_queue(self):
        """Poller loop"""
        self.logger.info("Database Job Worker Started")

        while not self._stop_event.is_set():
            db = SessionLocal()
            try:
                # Priority: SCAN -> THUMBNAIL -> CLEANUP
                job = db.query(ScanJob).filter(
                    ScanJob.status == JobStatus.PENDING,
                    ScanJob.job_type == JobType.SCAN
                ).order_by(asc(ScanJob.created_at)).first()

                if not job:
                    job = db.query(ScanJob).filter(
                        ScanJob.status == JobStatus.PENDING,
                        ScanJob.job_type == JobType.THUMBNAIL
                    ).order_by(asc(ScanJob.created_at)).first()

                if not job:
                    job = db.query(ScanJob).filter(
                        ScanJob.status == JobStatus.PENDING,
                        ScanJob.job_type == JobType.CLEANUP
                    ).order_by(asc(ScanJob.created_at)).first()

                if job:
                    # OPTIMIZATION: Atomic Claim
                    # To prevent race conditions between workers, we try to UPDATE the row.
                    # If the row was claimed by another worker in the split second between
                    # the query above and now, this UPDATE will return 0 rows affected.
                    rows_affected = db.query(ScanJob).filter(
                        ScanJob.id == job.id,
                        ScanJob.status == JobStatus.PENDING
                    ).update({"status": JobStatus.RUNNING, "started_at": datetime.now(timezone.utc)})

                    db.commit()

                    if rows_affected == 0:
                        db.close()
                        continue

                    # Extract data before closing session
                    job_data = {
                        "id": job.id,
                        "library_id": job.library_id,
                        "type": job.job_type,
                        "force": job.force_scan
                    }
                    db.close()

                    # Set Flag (using helper)
                    if job_data['library_id']:
                        self._set_library_scanning_status(job_data['library_id'], True)

                    # Execute
                    if job_data['type'] == JobType.SCAN:
                        self._run_scan_job(job_data)
                    elif job_data['type'] == JobType.THUMBNAIL:
                        self._run_thumbnail_job(job_data)
                    elif job_data['type'] == JobType.CLEANUP:
                        self._run_cleanup_job(job_data)

                else:
                    db.close()
                    time.sleep(2)

            except Exception as e:
                self.logger.error(f"Worker polling error: {e}")
                if db: db.close()
                time.sleep(5)

    def _run_scan_job(self, job_data):
        db = SessionLocal()
        job_id = job_data['id']
        library_id = job_data['library_id']
        force = job_data['force']

        try:
            library = db.query(Library).get(library_id)
            if not library:
                self.logger.error(f"Library {library_id} not found for job {job_id}")
                return

            is_first_scan = library.last_scanned is None
            self.logger.info(f"Starting SCAN job {job_id} for {library.name}")

            # --- RUN SCANNER ---
            scanner = LibraryScanner(library, db)
            results = scanner.scan(force=force)
            # -------------------

            # Update Job
            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
                "result_summary": json.dumps({
                    "imported": results.get("imported", 0),
                    "updated": results.get("updated", 0),
                    "deleted": results.get("deleted", 0),
                    "errors": results.get("errors", 0),
                    "elapsed": results.get("elapsed", 0)
                })
            })

            # --- QUEUE NEXT JOBS ---

            # Create Thumbnail Job
            self.logger.info(f"Scan complete. Queuing thumbnail generation for Library {library_id}")

            thumb_job = ScanJob(
                library_id=library_id,
                job_type=JobType.THUMBNAIL,
                force_scan=force,
                status=JobStatus.PENDING
            )
            db.add(thumb_job)

            # Cleanup Job (Only if NOT first scan)
            if not is_first_scan:
                self.logger.info(f"Queuing cleanup job for Library {library_id} (Not initial scan)")
                cleanup_job = ScanJob(
                    library_id=library_id,
                    job_type=JobType.CLEANUP,
                    status=JobStatus.PENDING
                )
                db.add(cleanup_job)
            else:
                self.logger.info(f"Skipping cleanup job for Library {library_id} (First Scan)")

            db.commit()

        except Exception as e:
            self.logger.error(f"Scan Job {job_id} Failed: {e}")

            traceback.print_exc()
            db.rollback()
            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.FAILED,
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc)
            })
            db.commit()
        finally:
            db.close()
            # Reset Flag safely outside main transaction
            self._set_library_scanning_status(library_id, False)

    def _run_thumbnail_job(self, job_data):
        db = SessionLocal()
        job_id = job_data['id']
        library_id = job_data['library_id']
        force = job_data['force']

        try:
            self.logger.info(f"Starting THUMBNAIL job {job_id}")

            service = ThumbnailService(db, library_id)
            use_parallel = get_cached_setting('system.parallel_image_processing', False)

            if use_parallel:
                stats = service.process_missing_thumbnails_parallel(force=force)
            else:
                stats = service.process_missing_thumbnails(force=force)

            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.COMPLETED,
                "result_summary": json.dumps(stats),
                "completed_at": datetime.now(timezone.utc)
            })
            db.commit()

        except Exception as e:
            self.logger.error(f"Thumbnail Job {job_id} Failed: {e}")
            traceback.print_exc()
            db.rollback()
            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.FAILED,
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc)
            })
            db.commit()
        finally:
            db.close()
            # Reset Flag safely
            self._set_library_scanning_status(library_id, False)

    def _run_cleanup_job(self, job_data):
        db = SessionLocal()
        job_id = job_data['id']
        library_id = job_data['library_id']

        try:
            context = f"Library {library_id}" if library_id else "GLOBAL"
            self.logger.info(f"Starting CLEANUP job {job_id} ({context})")

            # Logging context
            context_str = f"Library {library_id}" if library_id else "GLOBAL"
            self.logger.info(f"Starting CLEANUP job {job_id} ({context_str})")

            # --- RUN MAINTENANCE ---
            maintenance = MaintenanceService(db)

            # Pass library_id directly.
            # If None, MaintenanceService cleans EVERYTHING.
            # If Int, MaintenanceService cleans ONLY that library.
            stats = maintenance.cleanup_orphans(library_id=library_id)

            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.COMPLETED,
                "result_summary": json.dumps(stats),
                "completed_at": datetime.now(timezone.utc)
            })
            db.commit()

        except Exception as e:
            self.logger.error(f"Cleanup Job {job_id} Failed: {e}")
            db.rollback()
            db.query(ScanJob).filter(ScanJob.id == job_id).update({
                "status": JobStatus.FAILED,
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc)
            })
            db.commit()
        finally:
            db.close()
            # Reset Flag safely (only if library specific)
            if library_id:
                self._set_library_scanning_status(library_id, False)

    def add_cleanup_task(self) -> dict:
        """Queue a global cleanup task"""
        db = SessionLocal()
        try:
            # Check for existing pending cleanup to avoid stacking
            existing = db.query(ScanJob).filter(
                ScanJob.job_type == JobType.CLEANUP,
                ScanJob.status.in_([JobStatus.PENDING, JobStatus.RUNNING])
            ).first()

            if existing:
                return {"status": "ignored", "job_id": existing.id, "message": "Cleanup already queued"}

            job = ScanJob(library_id=None, job_type=JobType.CLEANUP, status=JobStatus.PENDING)
            db.add(job)
            db.commit()
            db.refresh(job)

            return {"status": "queued", "job_id": job.id, "message": "Global cleanup job queued"}
        finally:
            db.close()


# Global instance
scan_manager = ScanManager()