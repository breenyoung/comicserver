from sqlalchemy.orm import Session
from typing import List
from app.models.tags import Character, Team, Location


class TagService:
    """Service for managing tags (characters, teams, locations)"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_character(self, name: str) -> Character:
        """Get existing character or create new one"""
        name = name.strip()
        character = self.db.query(Character).filter(Character.name == name).first()

        if not character:
            character = Character(name=name)
            self.db.add(character)
            self.db.commit()
            self.db.refresh(character)

        return character

    def get_or_create_characters(self, names: str) -> List[Character]:
        """Parse comma-separated names and get/create characters"""
        if not names:
            return []

        # Split by comma and clean up, then deduplicate
        name_list = [n.strip() for n in names.split(',') if n.strip()]
        unique_names = list(dict.fromkeys(name_list))  # Deduplicate while preserving order

        characters = []
        for name in unique_names:
            characters.append(self.get_or_create_character(name))

        return characters

    def get_or_create_team(self, name: str) -> Team:
        """Get existing team or create new one"""
        name = name.strip()
        team = self.db.query(Team).filter(Team.name == name).first()

        if not team:
            team = Team(name=name)
            self.db.add(team)
            self.db.commit()
            self.db.refresh(team)

        return team

    def get_or_create_teams(self, names: str) -> List[Team]:
        """Parse comma-separated names and get/create teams"""
        if not names:
            return []

        # Split by comma and clean up, then deduplicate
        name_list = [n.strip() for n in names.split(',') if n.strip()]
        unique_names = list(dict.fromkeys(name_list))  # Deduplicate while preserving order

        teams = []
        for name in unique_names:
            teams.append(self.get_or_create_team(name))

        return teams

    def get_or_create_location(self, name: str) -> Location:
        """Get existing location or create new one"""
        name = name.strip()
        location = self.db.query(Location).filter(Location.name == name).first()

        if not location:
            location = Location(name=name)
            self.db.add(location)
            self.db.commit()
            self.db.refresh(location)

        return location

    def get_or_create_locations(self, names: str) -> List[Location]:
        """Parse comma-separated names and get/create locations"""
        if not names:
            return []

        # Split by comma and clean up, then deduplicate
        name_list = [n.strip() for n in names.split(',') if n.strip()]
        unique_names = list(dict.fromkeys(name_list))  # Deduplicate while preserving order

        locations = []
        for name in unique_names:
            locations.append(self.get_or_create_location(name))

        return locations