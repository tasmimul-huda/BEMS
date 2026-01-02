from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from app.models.base import BaseModel


class VoterDemographics(BaseModel):
    __tablename__ = "voter_demographics"
    
    constituency_id = Column(Integer, ForeignKey("constituency.id"), nullable=False)
    election_year = Column(Integer, nullable=False)
    
    # Total counts
    total_voters = Column(Integer, nullable=False)
    male_voters = Column(Integer, nullable=False, default=0)
    female_voters = Column(Integer, nullable=False, default=0)
    other_voters = Column(Integer, nullable=False, default=0)
    
    # Age groups
    age_18_25 = Column(Integer, default=0)
    age_26_35 = Column(Integer, default=0)
    age_36_45 = Column(Integer, default=0)
    age_46_55 = Column(Integer, default=0)
    age_56_65 = Column(Integer, default=0)
    age_66_plus = Column(Integer, default=0)
    
    # Other demographics
    religion_distribution = Column(JSON, nullable=True)  # {"islam": 85, "hindu": 12, ...}
    minority_groups = Column(JSON, nullable=True)
    
    # Update info
    last_updated = Column(DateTime, nullable=True)
    source = Column(String(200), nullable=True)
    
    # Relationships
    constituency = relationship("Constituency", back_populates="demographics")
    
    def __repr__(self):
        return f"<VoterDemographics {self.constituency_id} {self.election_year}>"


class PollingCenter(BaseModel):
    __tablename__ = "polling_center"
    
    name = Column(String(300), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    constituency_id = Column(Integer, ForeignKey("constituency.id"), nullable=False)
    location = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    total_voters = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    constituency = relationship("Constituency", back_populates="polling_centers")
    results = relationship("PollingCenterResult", back_populates="polling_center")
    
    def __repr__(self):
        return f"<PollingCenter {self.code}: {self.name}>"


class PollingCenterResult(BaseModel):
    __tablename__ = "polling_center_results"
    
    polling_center_id = Column(Integer, ForeignKey("polling_center.id"), nullable=False)
    candidate_id = Column(Integer, ForeignKey("candidate.id"), nullable=False)
    election_year = Column(Integer, nullable=False)
    
    # Votes
    votes_received = Column(Integer, nullable=False, default=0)
    vote_percentage = Column(Float, nullable=True)
    
    # Status
    is_valid = Column(Boolean, default=True)
    remarks = Column(Text, nullable=True)
    
    # Audit
    entered_by = Column(Integer, ForeignKey("admin_user.id"), nullable=True)
    verified_by = Column(Integer, ForeignKey("admin_user.id"), nullable=True)
    verification_time = Column(DateTime, nullable=True)
    
    # Relationships
    polling_center = relationship("PollingCenter", back_populates="results")
    candidate = relationship("Candidate", back_populates="polling_results")
    
    def __repr__(self):
        return f"<PollingCenterResult {self.polling_center_id}-{self.candidate_id}>"


class ConstituencyResult(BaseModel):
    __tablename__ = "constituency_results"
    
    constituency_id = Column(Integer, ForeignKey("constituency.id"), nullable=False)
    election_year = Column(Integer, nullable=False)
    election_type = Column(String(50), nullable=False)
    
    # Totals
    total_votes = Column(Integer, nullable=False)
    valid_votes = Column(Integer, nullable=False)
    rejected_votes = Column(Integer, nullable=False)
    turnout_percentage = Column(Float, nullable=False)
    
    # Winner info
    winning_candidate_id = Column(Integer, ForeignKey("candidate.id"), nullable=True)
    winning_party_id = Column(Integer, ForeignKey("party.id"), nullable=True)
    margin_votes = Column(Integer, nullable=True)
    margin_percentage = Column(Float, nullable=True)
    
    # Result status
    is_official = Column(Boolean, default=False)
    declared_at = Column(DateTime, nullable=True)
    
    # Relationships
    constituency = relationship("Constituency", back_populates="election_results")
    winning_candidate = relationship("Candidate", foreign_keys=[winning_candidate_id])
    winning_party = relationship("Party", foreign_keys=[winning_party_id])
    
    def __repr__(self):
        return f"<ConstituencyResult {self.constituency_id} {self.election_year}>"


class ImportLog(BaseModel):
    __tablename__ = "import_log"
    
    import_type = Column(String(50), nullable=False)  # constituency, candidate, results, etc.
    file_name = Column(String(500), nullable=False)
    total_rows = Column(Integer, nullable=False)
    successful_rows = Column(Integer, nullable=False)
    failed_rows = Column(Integer, nullable=False)
    errors = Column(JSON, nullable=True)  # Store error details
    user_id = Column(Integer, ForeignKey("admin_user.id"), nullable=False)
    status = Column(String(20), default="completed")  # pending, processing, completed, failed
    
    # Relationships
    user = relationship("AdminUser", back_populates="import_logs")
    
    def __repr__(self):
        return f"<ImportLog {self.import_type} {self.status}>"