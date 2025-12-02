from sqlalchemy.orm import Session

from app.models.tags import Character, Team, Location
from app.models.credits import Person
from app.models.reading_list import ReadingList
from app.models.collection import Collection

from app.services.enrichment import EnrichmentService

class MaintenanceService:
    def __init__(self, db: Session):
        self.db = db
        self.enrichment = EnrichmentService()

    def cleanup_orphans(self) -> dict:
        """
        Delete metadata entities that are no longer associated with any comics.
        """
        stats = {
            "characters": 0,
            "teams": 0,
            "locations": 0,
            "people": 0,
            "empty_lists": 0,
            "empty_collections": 0
        }

        # 1. Clean Tags (Characters)
        # Logic: Delete Character where NOT EXISTS (select 1 from comic_characters where character_id = characters.id)
        # SQLAlchemy efficient way:
        deleted = self.db.query(Character).filter(~Character.comics.any()).delete(synchronize_session=False)
        stats["characters"] = deleted

        # 2. Clean Teams
        deleted = self.db.query(Team).filter(~Team.comics.any()).delete(synchronize_session=False)
        stats["teams"] = deleted

        # 3. Clean Locations
        deleted = self.db.query(Location).filter(~Location.comics.any()).delete(synchronize_session=False)
        stats["locations"] = deleted

        # 4. Clean People (Credits)
        # A person is an orphan if they have no 'credits' entries
        deleted = self.db.query(Person).filter(~Person.credits.any()).delete(synchronize_session=False)
        stats["people"] = deleted

        # 5. Clean Empty Containers (Optional, but good hygiene)
        deleted = self.db.query(ReadingList).filter(~ReadingList.items.any()).filter(ReadingList.auto_generated == True).delete(synchronize_session=False)
        stats["empty_lists"] = deleted

        deleted = self.db.query(Collection).filter(~Collection.items.any()).filter(Collection.auto_generated == True).delete(synchronize_session=False)
        stats["empty_collections"] = deleted

        self.db.commit()
        return stats

    def refresh_reading_list_descriptions(self) -> dict:
        """
        Iterate over auto-generated reading lists and attempt to populate
        missing descriptions from the local seed file.
        """
        # Fetch lists that are auto-generated
        # Optimization: You could filter(ReadingList.description == None)
        # if you only want to fill gaps, but updating all allows you to
        # fix typos by updating events.json.
        lists = self.db.query(ReadingList).filter(ReadingList.auto_generated == True).all()

        updated_count = 0

        for r_list in lists:
            # Synchronous lookup from local JSON
            # We mock the async call since we know we are using the local sync method
            # If you kept the async definition in EnrichmentService, you might need
            # to run this loop differently, but for the local JSON version:

            # Note: accessing private/internal method directly for sync usage
            # or rely on the fact that get_description is effectively instant for local.
            # Assuming you simplified EnrichmentService to be synchronous as discussed:
            description = self.enrichment.get_description(r_list.name)

            if description and description != r_list.description:
                r_list.description = description
                updated_count += 1

        if updated_count > 0:
            self.db.commit()

        return {"updated": updated_count, "total_scanned": len(lists)}

