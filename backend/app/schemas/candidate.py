from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import date, datetime


class PartyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    acronym: Optional[str] = Field(None, max_length=50)
    symbol_name: Optional[str] = Field(None, max_length=100)
    symbol_image_url: Optional[str] = None
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_registered: bool = True


class PartyCreate(PartyBase):
    pass


class PartyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    acronym: Optional[str] = Field(None, max_length=50)
    symbol_name: Optional[str] = Field(None, max_length=100)
    symbol_image_url: Optional[str] = None
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")
    is_registered: Optional[bool] = None


class PartyInDB(PartyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CandidateBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    bengali_name: Optional[str] = Field(None, max_length=200)
    date_of_birth: Optional[date] = None
    age: Optional[int] = Field(None, ge=21, le=150)
    education: Optional[str] = Field(None, max_length=300)
    profession: Optional[str] = Field(None, max_length=200)
    party_id: int
    constituency_id: int
    election_year: int = Field(..., ge=1970, le=2100)
    election_type: str = Field(..., pattern="^(National|Local|Upazila|City)$")
    candidate_number: Optional[str] = Field(None, max_length=20)
    deposit_status: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = None
    symbol_image_url: Optional[str] = None
    is_active: bool = True


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    bengali_name: Optional[str] = Field(None, max_length=200)
    date_of_birth: Optional[date] = None
    age: Optional[int] = Field(None, ge=21, le=150)
    education: Optional[str] = Field(None, max_length=300)
    profession: Optional[str] = Field(None, max_length=200)
    party_id: Optional[int] = None
    constituency_id: Optional[int] = None
    election_year: Optional[int] = Field(None, ge=1970, le=2100)
    election_type: Optional[str] = Field(None, pattern="^(National|Local|Upazila|City)$")
    candidate_number: Optional[str] = Field(None, max_length=20)
    deposit_status: Optional[str] = Field(None, max_length=50)
    photo_url: Optional[str] = None
    symbol_image_url: Optional[str] = None
    is_active: Optional[bool] = None


class CandidateInDB(CandidateBase):
    id: int
    created_at: datetime
    updated_at: datetime
    party: Optional[PartyInDB] = None
    constituency: Optional[dict] = None
    
    model_config = ConfigDict(from_attributes=True)


class CandidateWithResults(CandidateInDB):
    polling_results: List[dict] = []
    total_votes: Optional[int] = None
    vote_percentage: Optional[float] = None