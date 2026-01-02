from sqlalchemy import Column, String, Integer, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Party(BaseModel):
    __tablename__ = "party"
    
    name = Column(String(200), nullable=False, unique=True, index=True)
    acronym = Column(String(50), nullable=True)
    symbol_name = Column(String(100), nullable=True)
    symbol_image_url = Column(String(500), nullable=True)
    color_code = Column(String(7), nullable=True)  # Hex color for maps
    is_registered = Column(Boolean, default=True)
    
    # Relationships
    candidates = relationship("Candidate", back_populates="party")
    
    def __repr__(self):
        return f"<Party {self.name}>"


class Candidate(BaseModel):
    __tablename__ = "candidate"
    
    # Personal Info
    full_name = Column(String(200), nullable=False, index=True)
    bengali_name = Column(String(200), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    age = Column(Integer, nullable=True)
    education = Column(String(300), nullable=True)
    profession = Column(String(200), nullable=True)
    
    # Election Info
    party_id = Column(Integer, ForeignKey("party.id"), nullable=False)
    constituency_id = Column(Integer, ForeignKey("constituency.id"), nullable=False)
    election_year = Column(Integer, nullable=False)
    election_type = Column(String(50), nullable=False)  # National, Local, etc.
    candidate_number = Column(String(20), nullable=True)
    deposit_status = Column(String(50), nullable=True)  # Forfeited, Returned
    
    # Media
    photo_url = Column(String(500), nullable=True)
    symbol_image_url = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Relationships
    party = relationship("Party", back_populates="candidates")
    constituency = relationship("Constituency", back_populates="candidates")
    polling_results = relationship("PollingCenterResult", back_populates="candidate")
    
    def __repr__(self):
        return f"<Candidate {self.full_name}>"