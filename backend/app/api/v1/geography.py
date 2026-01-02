from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import pandas as pd
import base64
import io

from app.database import get_db
from app.dependencies import require_data_entry_or_above, require_viewer_or_above
from app.crud.geography import crud_division, crud_district, crud_constituency
from app.schemas.geography import (
    DivisionCreate, DivisionUpdate, DivisionInDB,
    DistrictCreate, DistrictUpdate, DistrictInDB,
    ConstituencyCreate, ConstituencyUpdate, ConstituencyInDB,
    CSVImportResponse
)
from app.utils.csv_import import (
    validate_constituency_csv,
    import_constituency_data,
    validate_division_csv,
    import_division_data,
    validate_district_csv,
    import_district_data
)

router = APIRouter(prefix="/geography", tags=["geography"])


# Division endpoints
@router.post("/divisions/", response_model=DivisionInDB, status_code=status.HTTP_201_CREATED)
def create_division(
    division: DivisionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    return crud_division.create(db=db, obj_in=division)


@router.get("/divisions/", response_model=List[DivisionInDB])
def read_divisions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    return crud_division.get_multi(
        db, skip=skip, limit=limit, search=search
    )


@router.get("/divisions/{division_id}", response_model=DivisionInDB)
def read_division(
    division_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    division = crud_division.get(db, division_id=division_id)
    if not division:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Division not found"
        )
    return division


@router.put("/divisions/{division_id}", response_model=DivisionInDB)
def update_division(
    division_id: int,
    division_update: DivisionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    division = crud_division.get(db, division_id=division_id)
    if not division:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Division not found"
        )
    return crud_division.update(db=db, db_obj=division, obj_in=division_update)


@router.delete("/divisions/{division_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_division(
    division_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    crud_division.delete(db=db, division_id=division_id)
    return None


# District endpoints
@router.post("/districts/", response_model=DistrictInDB, status_code=status.HTTP_201_CREATED)
def create_district(
    district: DistrictCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    return crud_district.create(db=db, obj_in=district)


@router.get("/districts/", response_model=List[DistrictInDB])
def read_districts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    division_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    return crud_district.get_multi(
        db, skip=skip, limit=limit, division_id=division_id, search=search
    )


@router.get("/districts/{district_id}", response_model=DistrictInDB)
def read_district(
    district_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    district = crud_district.get(db, district_id=district_id)
    if not district:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District not found"
        )
    return district


@router.put("/districts/{district_id}", response_model=DistrictInDB)
def update_district(
    district_id: int,
    district_update: DistrictUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    district = crud_district.get(db, district_id=district_id)
    if not district:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="District not found"
        )
    return crud_district.update(db=db, db_obj=district, obj_in=district_update)


@router.delete("/districts/{district_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_district(
    district_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    crud_district.delete(db=db, district_id=district_id)
    return None


# Constituency endpoints
@router.post("/constituencies/", response_model=ConstituencyInDB, status_code=status.HTTP_201_CREATED)
def create_constituency(
    constituency: ConstituencyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    return crud_constituency.create(db=db, obj_in=constituency)


@router.get("/constituencies/", response_model=List[ConstituencyInDB])
def read_constituencies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    division_id: Optional[int] = Query(None),
    district_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    return crud_constituency.get_multi(
        db, skip=skip, limit=limit,
        division_id=division_id,
        district_id=district_id,
        search=search,
        is_active=is_active
    )


@router.get("/constituencies/{constituency_id}", response_model=ConstituencyInDB)
def read_constituency(
    constituency_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    constituency = crud_constituency.get(db, constituency_id=constituency_id)
    if not constituency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constituency not found"
        )
    return constituency


@router.get("/constituencies/{constituency_id}/stats")
def get_constituency_stats(
    constituency_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    return crud_constituency.get_stats(db, constituency_id=constituency_id)


@router.put("/constituencies/{constituency_id}", response_model=ConstituencyInDB)
def update_constituency(
    constituency_id: int,
    constituency_update: ConstituencyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    constituency = crud_constituency.get(db, constituency_id=constituency_id)
    if not constituency:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Constituency not found"
        )
    return crud_constituency.update(db=db, db_obj=constituency, obj_in=constituency_update)


@router.delete("/constituencies/{constituency_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_constituency(
    constituency_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    crud_constituency.delete(db=db, constituency_id=constituency_id)
    return None


# CSV Import endpoints
@router.post("/import/csv", response_model=CSVImportResponse)
async def import_csv(
    file: UploadFile = File(...),
    import_type: str = Query(..., pattern="^(division|district|constituency)$"),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    # Check file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are allowed"
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Parse CSV
        df = pd.read_csv(io.BytesIO(content))
        
        # Validate based on import type
        if import_type == "division":
            errors = validate_division_csv(df)
            if dry_run:
                return CSVImportResponse(
                    total_rows=len(df),
                    successful_rows=len(df) - len(errors),
                    failed_rows=len(errors),
                    errors=errors,
                    preview_data=df.head(10).to_dict('records')
                )
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"errors": errors}
                )
            result = import_division_data(db, df)
            
        elif import_type == "district":
            errors = validate_district_csv(df)
            if dry_run:
                return CSVImportResponse(
                    total_rows=len(df),
                    successful_rows=len(df) - len(errors),
                    failed_rows=len(errors),
                    errors=errors,
                    preview_data=df.head(10).to_dict('records')
                )
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"errors": errors}
                )
            result = import_district_data(db, df)
            
        elif import_type == "constituency":
            errors = validate_constituency_csv(df)
            if dry_run:
                return CSVImportResponse(
                    total_rows=len(df),
                    successful_rows=len(df) - len(errors),
                    failed_rows=len(errors),
                    errors=errors,
                    preview_data=df.head(10).to_dict('records')
                )
            if errors:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"errors": errors}
                )
            result = import_constituency_data(db, df)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing CSV: {str(e)}"
        )


@router.get("/hierarchy")
def get_geographic_hierarchy(
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get full geographic hierarchy for dropdowns/maps"""
    divisions = crud_division.get_multi(db, limit=1000)
    
    hierarchy = []
    for division in divisions:
        division_data = {
            "id": division.id,
            "name": division.name,
            "code": division.code,
            "districts": []
        }
        
        districts = crud_district.get_multi(db, division_id=division.id, limit=1000)
        for district in districts:
            district_data = {
                "id": district.id,
                "name": district.name,
                "code": district.code,
                "constituencies": []
            }
            
            constituencies = crud_constituency.get_multi(
                db, district_id=district.id, limit=1000
            )
            for constituency in constituencies:
                constituency_data = {
                    "id": constituency.id,
                    "name": constituency.name,
                    "number": constituency.number,
                    "total_voters": constituency.total_voters,
                    "is_active": constituency.is_active
                }
                district_data["constituencies"].append(constituency_data)
            
            division_data["districts"].append(district_data)
        
        hierarchy.append(division_data)
    
    return hierarchy