from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime


class VoterDemographicsBase(BaseModel):
    constituency_id: int
    election_year: int
    total_voters: int = Field(..., ge=0)
    male_voters: int = Field(0, ge=0)
    female_voters: int = Field(0, ge=0)
    other_voters: int = Field(0, ge=0)
    age_18_25: int = Field(0, ge=0)
    age_26_35: int = Field(0, ge=0)
    age_36_45: int = Field(0, ge=0)
    age_46_55: int = Field(0, ge=0)
    age_56_65: int = Field(0, ge=0)
    age_66_plus: int = Field(0, ge=0)
    religion_distribution: Optional[Dict[str, int]] = None
    minority_groups: Optional[Dict[str, int]] = None
    source: Optional[str] = None
    
    @field_validator('total_voters')
    @classmethod
    def validate_total_voters(cls, v, info):
        values = info.data
        total_gender = (values.get('male_voters', 0) + 
                       values.get('female_voters', 0) + 
                       values.get('other_voters', 0))
        if total_gender > v:
            raise ValueError('Sum of gender voters cannot exceed total voters')
        return v


class VoterDemographicsCreate(VoterDemographicsBase):
    pass


class VoterDemographicsUpdate(BaseModel):
    total_voters: Optional[int] = Field(None, ge=0)
    male_voters: Optional[int] = Field(None, ge=0)
    female_voters: Optional[int] = Field(None, ge=0)
    other_voters: Optional[int] = Field(None, ge=0)
    age_18_25: Optional[int] = Field(None, ge=0)
    age_26_35: Optional[int] = Field(None, ge=0)
    age_36_45: Optional[int] = Field(None, ge=0)
    age_46_55: Optional[int] = Field(None, ge=0)
    age_56_65: Optional[int] = Field(None, ge=0)
    age_66_plus: Optional[int] = Field(None, ge=0)
    religion_distribution: Optional[Dict[str, int]] = None
    minority_groups: Optional[Dict[str, int]] = None
    source: Optional[str] = None


class VoterDemographicsInDB(VoterDemographicsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_updated: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class PollingCenterBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    code: str = Field(..., min_length=2, max_length=50)
    constituency_id: int
    location: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    total_voters: Optional[int] = Field(None, ge=0)
    is_active: bool = True


class PollingCenterCreate(PollingCenterBase):
    pass


class PollingCenterUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    code: Optional[str] = Field(None, min_length=2, max_length=50)
    constituency_id: Optional[int] = None
    location: Optional[str] = Field(None, max_length=500)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    total_voters: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class PollingCenterInDB(PollingCenterBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class PollingCenterResultBase(BaseModel):
    polling_center_id: int
    candidate_id: int
    election_year: int
    votes_received: int = Field(..., ge=0)
    vote_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_valid: bool = True
    remarks: Optional[str] = None


class PollingCenterResultCreate(PollingCenterResultBase):
    pass


class PollingCenterResultUpdate(BaseModel):
    votes_received: Optional[int] = Field(None, ge=0)
    vote_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_valid: Optional[bool] = None
    remarks: Optional[str] = None


class PollingCenterResultInDB(PollingCenterResultBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ConstituencyResultBase(BaseModel):
    constituency_id: int
    election_year: int
    election_type: str
    total_votes: int = Field(..., ge=0)
    valid_votes: int = Field(..., ge=0)
    rejected_votes: int = Field(..., ge=0)
    turnout_percentage: float = Field(..., ge=0, le=100)
    winning_candidate_id: Optional[int] = None
    winning_party_id: Optional[int] = None
    margin_votes: Optional[int] = Field(None, ge=0)
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_official: bool = False
    
    @field_validator('total_votes')
    @classmethod
    def validate_votes(cls, v, info):
        values = info.data
        valid = values.get('valid_votes', 0)
        rejected = values.get('rejected_votes', 0)
        if valid + rejected != v:
            raise ValueError('Total votes must equal valid votes + rejected votes')
        return v


class ConstituencyResultCreate(ConstituencyResultBase):
    pass


class ConstituencyResultUpdate(BaseModel):
    total_votes: Optional[int] = Field(None, ge=0)
    valid_votes: Optional[int] = Field(None, ge=0)
    rejected_votes: Optional[int] = Field(None, ge=0)
    turnout_percentage: Optional[float] = Field(None, ge=0, le=100)
    winning_candidate_id: Optional[int] = None
    winning_party_id: Optional[int] = None
    margin_votes: Optional[int] = Field(None, ge=0)
    margin_percentage: Optional[float] = Field(None, ge=0, le=100)
    is_official: Optional[bool] = None
    declared_at: Optional[datetime] = None


class ConstituencyResultInDB(ConstituencyResultBase):
    id: int
    created_at: datetime
    updated_at: datetime
    declared_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class ElectionStatsResponse(BaseModel):
    total_constituencies: int
    total_candidates: int
    total_voters: int
    total_votes_cast: int
    overall_turnout: float
    leading_party: Optional[str] = None
    results_declared: int
    results_pending: int
    last_updated: datetime