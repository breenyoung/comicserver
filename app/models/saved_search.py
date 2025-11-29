from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)

    # We store the entire SearchRequest payload (filters, match, sort) as a JSON string
    query_json = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    user = relationship("User", backref="saved_searches")