from sqlalchemy import Boolean, Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON

from app.models.base import BaseModel


class Division(BaseModel):
    __tablename__ = "division"
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    code = Column(String(10), unique=True, nullable=False)
    bengali_name = Column(String(100), nullable=True)
    total_population = Column(Integer, nullable=True)
    total_voters = Column(Integer, nullable=True)
    
    # Relationships
    districts = relationship("District", back_populates="division")
    
    def __repr__(self):
        return f"<Division {self.name}>"


class District(BaseModel):
    __tablename__ = "district"
    
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(10), nullable=False)
    bengali_name = Column(String(100), nullable=True)
    division_id = Column(Integer, ForeignKey("division.id"), nullable=False)
    area_sq_km = Column(Integer, nullable=True)
    total_voters = Column(Integer, nullable=True)
    
    # Relationships
    division = relationship("Division", back_populates="districts")
    constituencies = relationship("Constituency", back_populates="district")
    
    def __repr__(self):
        return f"<District {self.name}>"


class Constituency(BaseModel):
    __tablename__ = "constituency"
    
    name = Column(String(200), nullable=False, index=True)
    number = Column(String(10), nullable=False)
    district_id = Column(Integer, ForeignKey("district.id"), nullable=False)
    area_description = Column(Text, nullable=True)
    geo_boundary = Column(JSON, nullable=True)  # GeoJSON data
    total_voters = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    district = relationship("District", back_populates="constituencies")
    candidates = relationship("Candidate", back_populates="constituency")
    polling_centers = relationship("PollingCenter", back_populates="constituency")
    demographics = relationship("VoterDemographics", back_populates="constituency")
    election_results = relationship("ConstituencyResult", back_populates="constituency")
    
    def __repr__(self):
        return f"<Constituency {self.number}: {self.name}>"
    
