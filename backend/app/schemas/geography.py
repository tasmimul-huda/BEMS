from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from typing import List


class DivisionBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)
    bengali_name: Optional[str] = Field(None, max_length=100)
    total_population: Optional[int] = None
    total_voters: Optional[int] = None


class DivisionCreate(DivisionBase):
    pass


class DivisionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    bengali_name: Optional[str] = Field(None, max_length=100)
    total_population: Optional[int] = None
    total_voters: Optional[int] = None


class DivisionInDB(DivisionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DistrictBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=10)
    bengali_name: Optional[str] = Field(None, max_length=100)
    division_id: int
    area_sq_km: Optional[int] = None
    total_voters: Optional[int] = None


class DistrictCreate(DistrictBase):
    pass


class DistrictUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    code: Optional[str] = Field(None, min_length=2, max_length=10)
    bengali_name: Optional[str] = Field(None, max_length=100)
    division_id: Optional[int] = None
    area_sq_km: Optional[int] = None
    total_voters: Optional[int] = None


class DistrictInDB(DistrictBase):
    id: int
    created_at: datetime
    updated_at: datetime
    division: Optional[DivisionInDB] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConstituencyBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    number: str = Field(..., min_length=1, max_length=10)
    district_id: int
    area_description: Optional[str] = None
    total_voters: Optional[int] = None
    is_active: bool = True


class ConstituencyCreate(ConstituencyBase):
    pass


class ConstituencyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    number: Optional[str] = Field(None, min_length=1, max_length=10)
    district_id: Optional[int] = None
    area_description: Optional[str] = None
    total_voters: Optional[int] = None
    is_active: Optional[bool] = None


class ConstituencyInDB(ConstituencyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    district: Optional[DistrictInDB] = None
    
    model_config = ConfigDict(from_attributes=True)


class ConstituencyWithResults(ConstituencyInDB):
    election_results: List[Any] = []


class CSVImportRequest(BaseModel):
    file_content: str  # Base64 encoded CSV content
    import_type: str = Field(..., pattern="^(division|district|constituency)$")
    dry_run: bool = False


class CSVImportResponse(BaseModel):
    total_rows: int
    successful_rows: int
    failed_rows: int
    errors: List[Dict[str, Any]] = []
    preview_data: Optional[List[Dict[str, Any]]] = None