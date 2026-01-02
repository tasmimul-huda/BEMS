import pandas as pd
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.crud.geography import crud_division, crud_district, crud_constituency
from app.schemas.geography import DivisionCreate, DistrictCreate, ConstituencyCreate
from app.models.geography import Division, District, Constituency

def validate_division_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate division CSV data"""
    errors = []
    required_columns = {"name", "code"}
    
    # Check required columns
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2  # Account for header row
        
        # Check required fields
        if pd.isna(row.get("name")) or str(row["name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "name",
                "error": "Division name is required"
            })
        
        if pd.isna(row.get("code")) or str(row["code"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "code",
                "error": "Division code is required"
            })
        
        # Check for duplicate codes in CSV
        if "code" in df.columns:
            code_counts = df["code"].value_counts()
            if code_counts[row["code"]] > 1:
                errors.append({
                    "row": row_num,
                    "column": "code",
                    "error": f"Duplicate division code: {row['code']}"
                })
    
    return errors


def validate_district_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate district CSV data"""
    errors = []
    required_columns = {"name", "code", "division_name"}
    
    # Check required columns
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        # Check required fields
        if pd.isna(row.get("name")) or str(row["name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "name",
                "error": "District name is required"
            })
        
        if pd.isna(row.get("code")) or str(row["code"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "code",
                "error": "District code is required"
            })
        
        if pd.isna(row.get("division_name")) or str(row["division_name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "division_name",
                "error": "Division name is required"
            })
    
    return errors


def validate_constituency_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate constituency CSV data"""
    errors = []
    required_columns = {"name", "number", "district_name", "division_name"}
    
    # Check required columns
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    # Validate each row
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        # Check required fields
        if pd.isna(row.get("name")) or str(row["name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "name",
                "error": "Constituency name is required"
            })
        
        if pd.isna(row.get("number")) or str(row["number"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "number",
                "error": "Constituency number is required"
            })
        
        if pd.isna(row.get("district_name")) or str(row["district_name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "district_name",
                "error": "District name is required"
            })
        
        if pd.isna(row.get("division_name")) or str(row["division_name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "division_name",
                "error": "Division name is required"
            })
    
    return errors


def import_division_data(db: Session, df: pd.DataFrame) -> Dict[str, Any]:
    """Import division data from CSV"""
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Check if division already exists
            existing = crud_division.get_by_code(db, code=str(row["code"]).strip())
            if existing:
                # Update existing
                update_data = {
                    "name": str(row["name"]).strip(),
                    "bengali_name": str(row["bengali_name"]).strip() if "bengali_name" in row else None,
                    "total_population": int(row["total_population"]) if "total_population" in row and pd.notna(row["total_population"]) else None,
                    "total_voters": int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None
                }
                crud_division.update(db, db_obj=existing, obj_in=update_data)
            else:
                # Create new
                division_data = DivisionCreate(
                    name=str(row["name"]).strip(),
                    code=str(row["code"]).strip(),
                    bengali_name=str(row["bengali_name"]).strip() if "bengali_name" in row else None,
                    total_population=int(row["total_population"]) if "total_population" in row and pd.notna(row["total_population"]) else None,
                    total_voters=int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None
                )
                crud_division.create(db, obj_in=division_data)
            
            successful += 1
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def import_district_data(db: Session, df: pd.DataFrame) -> Dict[str, Any]:
    """Import district data from CSV"""
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get division
            division_name = str(row["division_name"]).strip()
            division = db.query(Division).filter(Division.name == division_name).first()
            
            if not division:
                errors.append({
                    "row": idx + 2,
                    "error": f"Division not found: {division_name}"
                })
                failed += 1
                continue
            
            # Check if district already exists
            existing = db.query(District).filter(
                District.code == str(row["code"]).strip(),
                District.division_id == division.id
            ).first()
            
            if existing:
                # Update existing
                update_data = {
                    "name": str(row["name"]).strip(),
                    "bengali_name": str(row["bengali_name"]).strip() if "bengali_name" in row else None,
                    "area_sq_km": int(row["area_sq_km"]) if "area_sq_km" in row and pd.notna(row["area_sq_km"]) else None,
                    "total_voters": int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None
                }
                crud_district.update(db, db_obj=existing, obj_in=update_data)
            else:
                # Create new
                district_data = DistrictCreate(
                    name=str(row["name"]).strip(),
                    code=str(row["code"]).strip(),
                    bengali_name=str(row["bengali_name"]).strip() if "bengali_name" in row else None,
                    division_id=division.id,
                    area_sq_km=int(row["area_sq_km"]) if "area_sq_km" in row and pd.notna(row["area_sq_km"]) else None,
                    total_voters=int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None
                )
                crud_district.create(db, obj_in=district_data)
            
            successful += 1
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def import_constituency_data(db: Session, df: pd.DataFrame) -> Dict[str, Any]:
    """Import constituency data from CSV"""
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get division and district
            division_name = str(row["division_name"]).strip()
            district_name = str(row["district_name"]).strip()
            
            division = db.query(Division).filter(Division.name == division_name).first()
            if not division:
                errors.append({
                    "row": idx + 2,
                    "error": f"Division not found: {division_name}"
                })
                failed += 1
                continue
            
            district = db.query(District).filter(
                District.name == district_name,
                District.division_id == division.id
            ).first()
            
            if not district:
                errors.append({
                    "row": idx + 2,
                    "error": f"District not found: {district_name} in {division_name}"
                })
                failed += 1
                continue
            
            # Check if constituency already exists
            existing = db.query(Constituency).filter(
                Constituency.number == str(row["number"]).strip(),
                Constituency.district_id == district.id
            ).first()
            
            if existing:
                # Update existing
                update_data = {
                    "name": str(row["name"]).strip(),
                    "area_description": str(row["area_description"]).strip() if "area_description" in row else None,
                    "total_voters": int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None,
                    "is_active": bool(row["is_active"]) if "is_active" in row else True
                }
                crud_constituency.update(db, db_obj=existing, obj_in=update_data)
            else:
                # Create new
                constituency_data = ConstituencyCreate(
                    name=str(row["name"]).strip(),
                    number=str(row["number"]).strip(),
                    district_id=district.id,
                    area_description=str(row["area_description"]).strip() if "area_description" in row else None,
                    total_voters=int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None,
                    is_active=bool(row["is_active"]) if "is_active" in row else True
                )
                crud_constituency.create(db, obj_in=constituency_data)
            
            successful += 1
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }





def validate_candidate_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate candidate CSV data"""
    errors = []
    required_columns = {"full_name", "party_name", "constituency_number", "election_year", "election_type"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        # Check required fields
        for col in required_columns:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                errors.append({
                    "row": row_num,
                    "column": col,
                    "error": f"{col.replace('_', ' ').title()} is required"
                })
        
        # Validate election year
        if "election_year" in df.columns and pd.notna(row.get("election_year")):
            try:
                year = int(row["election_year"])
                if year < 1970 or year > 2100:
                    errors.append({
                        "row": row_num,
                        "column": "election_year",
                        "error": "Election year must be between 1970 and 2100"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "election_year",
                    "error": "Election year must be a valid number"
                })
        
        # Validate age if provided
        if "age" in df.columns and pd.notna(row.get("age")):
            try:
                age = int(row["age"])
                if age < 21 or age > 150:
                    errors.append({
                        "row": row_num,
                        "column": "age",
                        "error": "Age must be between 21 and 150"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "age",
                    "error": "Age must be a valid number"
                })
    
    return errors

from app.models.candidate import Candidate

def import_candidate_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import candidate data from CSV"""
    from app.models.candidate import Party
    from app.models.geography import Constituency
    from app.crud.candidate import crud_candidate
    from app.schemas.candidate import CandidateCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get party
            party_name = str(row["party_name"]).strip()
            party = db.query(Party).filter(Party.name == party_name).first()
            
            if not party:
                errors.append({
                    "row": idx + 2,
                    "error": f"Party not found: {party_name}"
                })
                failed += 1
                continue
            
            # Get constituency
            constituency_number = str(row["constituency_number"]).strip()
            constituency = db.query(Constituency).filter(Constituency.number == constituency_number).first()
            
            if not constituency:
                errors.append({
                    "row": idx + 2,
                    "error": f"Constituency not found: {constituency_number}"
                })
                failed += 1
                continue
            
            # Check if candidate already exists
            existing = db.query(Candidate).filter(
                Candidate.full_name == str(row["full_name"]).strip(),
                Candidate.constituency_id == constituency.id,
                Candidate.election_year == int(row["election_year"])
            ).first()
            
            if existing:
                # Update existing candidate
                update_data = {
                    "bengali_name": str(row["bengali_name"]).strip() if "bengali_name" in row and pd.notna(row["bengali_name"]) else None,
                    "age": int(row["age"]) if "age" in row and pd.notna(row["age"]) else None,
                    "education": str(row["education"]).strip() if "education" in row and pd.notna(row["education"]) else None,
                    "profession": str(row["profession"]).strip() if "profession" in row and pd.notna(row["profession"]) else None,
                    "candidate_number": str(row["candidate_number"]).strip() if "candidate_number" in row and pd.notna(row["candidate_number"]) else None,
                    "deposit_status": str(row["deposit_status"]).strip() if "deposit_status" in row and pd.notna(row["deposit_status"]) else None,
                    "party_id": party.id,
                    "is_active": bool(row["is_active"]) if "is_active" in row else True
                }
                
                for field, value in update_data.items():
                    setattr(existing, field, value)
                
                db.add(existing)
                successful += 1
            else:
                # Create new candidate
                candidate_data = CandidateCreate(
                    full_name=str(row["full_name"]).strip(),
                    bengali_name=str(row["bengali_name"]).strip() if "bengali_name" in row and pd.notna(row["bengali_name"]) else None,
                    age=int(row["age"]) if "age" in row and pd.notna(row["age"]) else None,
                    education=str(row["education"]).strip() if "education" in row and pd.notna(row["education"]) else None,
                    profession=str(row["profession"]).strip() if "profession" in row and pd.notna(row["profession"]) else None,
                    party_id=party.id,
                    constituency_id=constituency.id,
                    election_year=int(row["election_year"]),
                    election_type=str(row["election_type"]).strip(),
                    candidate_number=str(row["candidate_number"]).strip() if "candidate_number" in row and pd.notna(row["candidate_number"]) else None,
                    deposit_status=str(row["deposit_status"]).strip() if "deposit_status" in row and pd.notna(row["deposit_status"]) else None,
                    is_active=bool(row["is_active"]) if "is_active" in row else True
                )
                
                crud_candidate.create(db, obj_in=candidate_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def validate_party_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate party CSV data"""
    errors = []
    required_columns = {"name"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        if pd.isna(row.get("name")) or str(row["name"]).strip() == "":
            errors.append({
                "row": row_num,
                "column": "name",
                "error": "Party name is required"
            })
    
    return errors

from app.models.candidate import Party
def import_party_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import party data from CSV"""
    from app.crud.candidate import crud_party
    from app.schemas.candidate import PartyCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            party_name = str(row["name"]).strip()
            
            # Check if party exists
            existing = db.query(Party).filter(Party.name == party_name).first()
            
            if existing:
                # Update existing party
                update_data = {
                    "acronym": str(row["acronym"]).strip() if "acronym" in row and pd.notna(row["acronym"]) else None,
                    "symbol_name": str(row["symbol_name"]).strip() if "symbol_name" in row and pd.notna(row["symbol_name"]) else None,
                    "color_code": str(row["color_code"]).strip() if "color_code" in row and pd.notna(row["color_code"]) else None,
                    "is_registered": bool(row["is_registered"]) if "is_registered" in row else True
                }
                
                for field, value in update_data.items():
                    setattr(existing, field, value)
                
                db.add(existing)
                successful += 1
            else:
                # Create new party
                party_data = PartyCreate(
                    name=party_name,
                    acronym=str(row["acronym"]).strip() if "acronym" in row and pd.notna(row["acronym"]) else None,
                    symbol_name=str(row["symbol_name"]).strip() if "symbol_name" in row and pd.notna(row["symbol_name"]) else None,
                    color_code=str(row["color_code"]).strip() if "color_code" in row and pd.notna(row["color_code"]) else None,
                    is_registered=bool(row["is_registered"]) if "is_registered" in row else True
                )
                
                crud_party.create(db, obj_in=party_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def validate_polling_center_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate polling center CSV data"""
    errors = []
    required_columns = {"code", "name", "constituency_number"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        for col in required_columns:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                errors.append({
                    "row": row_num,
                    "column": col,
                    "error": f"{col.replace('_', ' ').title()} is required"
                })
        
        # Validate coordinates if provided
        if "latitude" in df.columns and pd.notna(row.get("latitude")):
            try:
                lat = float(row["latitude"])
                if lat < -90 or lat > 90:
                    errors.append({
                        "row": row_num,
                        "column": "latitude",
                        "error": "Latitude must be between -90 and 90"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "latitude",
                    "error": "Latitude must be a valid number"
                })
        
        if "longitude" in df.columns and pd.notna(row.get("longitude")):
            try:
                lon = float(row["longitude"])
                if lon < -180 or lon > 180:
                    errors.append({
                        "row": row_num,
                        "column": "longitude",
                        "error": "Longitude must be between -180 and 180"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "longitude",
                    "error": "Longitude must be a valid number"
                })
    
    return errors

from app.models.election import PollingCenter
def import_polling_center_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import polling center data from CSV"""
    from app.models.geography import Constituency
    from app.crud.election import crud_polling_center
    from app.schemas.election import PollingCenterCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get constituency
            constituency_number = str(row["constituency_number"]).strip()
            constituency = db.query(Constituency).filter(Constituency.number == constituency_number).first()
            
            if not constituency:
                errors.append({
                    "row": idx + 2,
                    "error": f"Constituency not found: {constituency_number}"
                })
                failed += 1
                continue
            
            # Check if polling center exists
            existing = db.query(PollingCenter).filter(PollingCenter.code == str(row["code"]).strip()).first()
            
            if existing:
                # Update existing
                update_data = {
                    "name": str(row["name"]).strip(),
                    "constituency_id": constituency.id,
                    "location": str(row["location"]).strip() if "location" in row and pd.notna(row["location"]) else None,
                    "latitude": float(row["latitude"]) if "latitude" in row and pd.notna(row["latitude"]) else None,
                    "longitude": float(row["longitude"]) if "longitude" in row and pd.notna(row["longitude"]) else None,
                    "total_voters": int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None,
                    "is_active": bool(row["is_active"]) if "is_active" in row else True
                }
                
                for field, value in update_data.items():
                    setattr(existing, field, value)
                
                db.add(existing)
                successful += 1
            else:
                # Create new
                center_data = PollingCenterCreate(
                    code=str(row["code"]).strip(),
                    name=str(row["name"]).strip(),
                    constituency_id=constituency.id,
                    location=str(row["location"]).strip() if "location" in row and pd.notna(row["location"]) else None,
                    latitude=float(row["latitude"]) if "latitude" in row and pd.notna(row["latitude"]) else None,
                    longitude=float(row["longitude"]) if "longitude" in row and pd.notna(row["longitude"]) else None,
                    total_voters=int(row["total_voters"]) if "total_voters" in row and pd.notna(row["total_voters"]) else None,
                    is_active=bool(row["is_active"]) if "is_active" in row else True
                )
                
                crud_polling_center.create(db, obj_in=center_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def validate_polling_result_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate polling result CSV data"""
    errors = []
    required_columns = {"polling_center_code", "candidate_name", "constituency_number", "election_year", "votes_received"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        for col in required_columns:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                errors.append({
                    "row": row_num,
                    "column": col,
                    "error": f"{col.replace('_', ' ').title()} is required"
                })
        
        # Validate votes
        if "votes_received" in df.columns and pd.notna(row.get("votes_received")):
            try:
                votes = int(row["votes_received"])
                if votes < 0:
                    errors.append({
                        "row": row_num,
                        "column": "votes_received",
                        "error": "Votes must be non-negative"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "votes_received",
                    "error": "Votes must be a valid integer"
                })
    
    return errors

from app.models.election import PollingCenterResult

def import_polling_result_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import polling result data from CSV"""
    from app.models.election import PollingCenter
    from app.models.candidate import Candidate
    from app.models.geography import Constituency
    from app.crud.election import crud_polling_result
    from app.schemas.election import PollingCenterResultCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get polling center
            center_code = str(row["polling_center_code"]).strip()
            polling_center = db.query(PollingCenter).filter(PollingCenter.code == center_code).first()
            
            if not polling_center:
                errors.append({
                    "row": idx + 2,
                    "error": f"Polling center not found: {center_code}"
                })
                failed += 1
                continue
            
            # Get constituency
            constituency_number = str(row["constituency_number"]).strip()
            constituency = db.query(Constituency).filter(Constituency.number == constituency_number).first()
            
            if not constituency:
                errors.append({
                    "row": idx + 2,
                    "error": f"Constituency not found: {constituency_number}"
                })
                failed += 1
                continue
            
            # Get candidate
            candidate_name = str(row["candidate_name"]).strip()
            election_year = int(row["election_year"])
            
            candidate = db.query(Candidate).filter(
                Candidate.full_name == candidate_name,
                Candidate.constituency_id == constituency.id,
                Candidate.election_year == election_year
            ).first()
            
            if not candidate:
                errors.append({
                    "row": idx + 2,
                    "error": f"Candidate not found: {candidate_name} in constituency {constituency_number} for year {election_year}"
                })
                failed += 1
                continue
            
            # Check if result exists
            existing = db.query(PollingCenterResult).filter(
                PollingCenterResult.polling_center_id == polling_center.id,
                PollingCenterResult.candidate_id == candidate.id,
                PollingCenterResult.election_year == election_year
            ).first()
            
            if existing:
                # Update existing
                existing.votes_received = int(row["votes_received"])
                existing.vote_percentage = None  # Will be recalculated
                db.add(existing)
                successful += 1
            else:
                # Create new
                result_data = PollingCenterResultCreate(
                    polling_center_id=polling_center.id,
                    candidate_id=candidate.id,
                    election_year=election_year,
                    votes_received=int(row["votes_received"]),
                    is_valid=bool(row["is_valid"]) if "is_valid" in row else True,
                    remarks=str(row["remarks"]).strip() if "remarks" in row and pd.notna(row["remarks"]) else None
                )
                
                crud_polling_result.create(db, obj_in=result_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def validate_voter_demographics_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate voter demographics CSV data"""
    errors = []
    required_columns = {"constituency_number", "election_year", "total_voters"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        for col in required_columns:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                errors.append({
                    "row": row_num,
                    "column": col,
                    "error": f"{col.replace('_', ' ').title()} is required"
                })
        
        # Validate numeric fields
        numeric_fields = ["total_voters", "male_voters", "female_voters", "other_voters"]
        for field in numeric_fields:
            if field in df.columns and pd.notna(row.get(field)):
                try:
                    value = int(row[field])
                    if value < 0:
                        errors.append({
                            "row": row_num,
                            "column": field,
                            "error": f"{field.replace('_', ' ').title()} must be non-negative"
                        })
                except ValueError:
                    errors.append({
                        "row": row_num,
                        "column": field,
                        "error": f"{field.replace('_', ' ').title()} must be a valid integer"
                    })
    
    return errors


from app.models.election import VoterDemographics
from datetime import datetime

def import_voter_demographics_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import voter demographics data from CSV"""
    from app.models.geography import Constituency
    from app.crud.election import crud_voter_demographics
    from app.schemas.election import VoterDemographicsCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get constituency
            constituency_number = str(row["constituency_number"]).strip()
            constituency = db.query(Constituency).filter(Constituency.number == constituency_number).first()
            
            if not constituency:
                errors.append({
                    "row": idx + 2,
                    "error": f"Constituency not found: {constituency_number}"
                })
                failed += 1
                continue
            
            election_year = int(row["election_year"])
            
            # Check if demographics exists
            existing = db.query(VoterDemographics).filter(
                VoterDemographics.constituency_id == constituency.id,
                VoterDemographics.election_year == election_year
            ).first()
            
            if existing:
                # Update existing
                update_data = {
                    "total_voters": int(row["total_voters"]),
                    "male_voters": int(row["male_voters"]) if "male_voters" in row and pd.notna(row["male_voters"]) else 0,
                    "female_voters": int(row["female_voters"]) if "female_voters" in row and pd.notna(row["female_voters"]) else 0,
                    "other_voters": int(row["other_voters"]) if "other_voters" in row and pd.notna(row["other_voters"]) else 0,
                    "age_18_25": int(row["age_18_25"]) if "age_18_25" in row and pd.notna(row["age_18_25"]) else 0,
                    "age_26_35": int(row["age_26_35"]) if "age_26_35" in row and pd.notna(row["age_26_35"]) else 0,
                    "age_36_45": int(row["age_36_45"]) if "age_36_45" in row and pd.notna(row["age_36_45"]) else 0,
                    "age_46_55": int(row["age_46_55"]) if "age_46_55" in row and pd.notna(row["age_46_55"]) else 0,
                    "age_56_65": int(row["age_56_65"]) if "age_56_65" in row and pd.notna(row["age_56_65"]) else 0,
                    "age_66_plus": int(row["age_66_plus"]) if "age_66_plus" in row and pd.notna(row["age_66_plus"]) else 0,
                    "source": str(row["source"]).strip() if "source" in row and pd.notna(row["source"]) else None
                }
                
                # Validate gender totals
                gender_total = (update_data["male_voters"] + update_data["female_voters"] + update_data["other_voters"])
                if gender_total > update_data["total_voters"]:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Sum of gender voters ({gender_total}) exceeds total voters ({update_data['total_voters']})"
                    })
                    failed += 1
                    continue
                
                for field, value in update_data.items():
                    setattr(existing, field, value)
                
                existing.last_updated = datetime.utcnow()
                db.add(existing)
                successful += 1
            else:
                # Create new
                demographics_data = VoterDemographicsCreate(
                    constituency_id=constituency.id,
                    election_year=election_year,
                    total_voters=int(row["total_voters"]),
                    male_voters=int(row["male_voters"]) if "male_voters" in row and pd.notna(row["male_voters"]) else 0,
                    female_voters=int(row["female_voters"]) if "female_voters" in row and pd.notna(row["female_voters"]) else 0,
                    other_voters=int(row["other_voters"]) if "other_voters" in row and pd.notna(row["other_voters"]) else 0,
                    age_18_25=int(row["age_18_25"]) if "age_18_25" in row and pd.notna(row["age_18_25"]) else 0,
                    age_26_35=int(row["age_26_35"]) if "age_26_35" in row and pd.notna(row["age_26_35"]) else 0,
                    age_36_45=int(row["age_36_45"]) if "age_36_45" in row and pd.notna(row["age_36_45"]) else 0,
                    age_46_55=int(row["age_46_55"]) if "age_46_55" in row and pd.notna(row["age_46_55"]) else 0,
                    age_56_65=int(row["age_56_65"]) if "age_56_65" in row and pd.notna(row["age_56_65"]) else 0,
                    age_66_plus=int(row["age_66_plus"]) if "age_66_plus" in row and pd.notna(row["age_66_plus"]) else 0,
                    source=str(row["source"]).strip() if "source" in row and pd.notna(row["source"]) else None
                )
                
                # Validate gender totals
                gender_total = (demographics_data.male_voters + demographics_data.female_voters + demographics_data.other_voters)
                if gender_total > demographics_data.total_voters:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Sum of gender voters ({gender_total}) exceeds total voters ({demographics_data.total_voters})"
                    })
                    failed += 1
                    continue
                
                crud_voter_demographics.create(db, obj_in=demographics_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }


def validate_constituency_result_csv(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Validate constituency result CSV data"""
    errors = []
    required_columns = {"constituency_number", "election_year", "total_votes", "valid_votes", "rejected_votes", "turnout_percentage"}
    
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        errors.append({
            "row": 0,
            "column": ",".join(missing_columns),
            "error": f"Missing required columns: {', '.join(missing_columns)}"
        })
        return errors
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        
        for col in required_columns:
            if pd.isna(row.get(col)) or str(row[col]).strip() == "":
                errors.append({
                    "row": row_num,
                    "column": col,
                    "error": f"{col.replace('_', ' ').title()} is required"
                })
        
        # Validate totals
        if all(field in df.columns for field in ["total_votes", "valid_votes", "rejected_votes"]):
            try:
                total = int(row["total_votes"])
                valid = int(row["valid_votes"])
                rejected = int(row["rejected_votes"])
                
                if valid + rejected != total:
                    errors.append({
                        "row": row_num,
                        "column": "total_votes,valid_votes,rejected_votes",
                        "error": f"Valid votes ({valid}) + Rejected votes ({rejected}) must equal Total votes ({total})"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "total_votes,valid_votes,rejected_votes",
                    "error": "Vote counts must be valid integers"
                })
        
        # Validate turnout percentage
        if "turnout_percentage" in df.columns and pd.notna(row.get("turnout_percentage")):
            try:
                turnout = float(row["turnout_percentage"])
                if turnout < 0 or turnout > 100:
                    errors.append({
                        "row": row_num,
                        "column": "turnout_percentage",
                        "error": "Turnout percentage must be between 0 and 100"
                    })
            except ValueError:
                errors.append({
                    "row": row_num,
                    "column": "turnout_percentage",
                    "error": "Turnout percentage must be a valid number"
                })
    
    return errors

from app.models.election import ConstituencyResult


def import_constituency_result_data(db: Session, df: pd.DataFrame, user_id: int) -> Dict[str, Any]:
    """Import constituency result data from CSV"""
    from app.models.geography import Constituency
    from app.models.candidate import Candidate, Party
    from app.crud.election import crud_constituency_result
    from app.schemas.election import ConstituencyResultCreate
    
    successful = 0
    failed = 0
    errors = []
    
    for idx, row in df.iterrows():
        try:
            # Get constituency
            constituency_number = str(row["constituency_number"]).strip()
            constituency = db.query(Constituency).filter(Constituency.number == constituency_number).first()
            
            if not constituency:
                errors.append({
                    "row": idx + 2,
                    "error": f"Constituency not found: {constituency_number}"
                })
                failed += 1
                continue
            
            election_year = int(row["election_year"])
            election_type = str(row.get("election_type", "National")).strip()
            
            # Get winning candidate if specified
            winning_candidate = None
            if "winning_candidate_name" in row and pd.notna(row["winning_candidate_name"]):
                candidate_name = str(row["winning_candidate_name"]).strip()
                winning_candidate = db.query(Candidate).filter(
                    Candidate.full_name == candidate_name,
                    Candidate.constituency_id == constituency.id,
                    Candidate.election_year == election_year
                ).first()
                
                if not winning_candidate:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Winning candidate not found: {candidate_name}"
                    })
                    failed += 1
                    continue
            
            # Get winning party if specified
            winning_party = None
            if "winning_party_name" in row and pd.notna(row["winning_party_name"]):
                party_name = str(row["winning_party_name"]).strip()
                winning_party = db.query(Party).filter(Party.name == party_name).first()
                
                if not winning_party:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Winning party not found: {party_name}"
                    })
                    failed += 1
                    continue
            
            # Check if result exists
            existing = db.query(ConstituencyResult).filter(
                ConstituencyResult.constituency_id == constituency.id,
                ConstituencyResult.election_year == election_year,
                ConstituencyResult.election_type == election_type
            ).first()
            
            if existing:
                # Update existing
                update_data = {
                    "total_votes": int(row["total_votes"]),
                    "valid_votes": int(row["valid_votes"]),
                    "rejected_votes": int(row["rejected_votes"]),
                    "turnout_percentage": float(row["turnout_percentage"]),
                    "winning_candidate_id": winning_candidate.id if winning_candidate else None,
                    "winning_party_id": winning_party.id if winning_party else None,
                    "margin_votes": int(row["margin_votes"]) if "margin_votes" in row and pd.notna(row["margin_votes"]) else None,
                    "margin_percentage": float(row["margin_percentage"]) if "margin_percentage" in row and pd.notna(row["margin_percentage"]) else None,
                    "is_official": bool(row["is_official"]) if "is_official" in row else False,
                    "declared_at": datetime.utcnow() if row.get("is_official") == True else None
                }
                
                # Validate vote totals
                if update_data["valid_votes"] + update_data["rejected_votes"] != update_data["total_votes"]:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Valid votes ({update_data['valid_votes']}) + Rejected votes ({update_data['rejected_votes']}) must equal Total votes ({update_data['total_votes']})"
                    })
                    failed += 1
                    continue
                
                for field, value in update_data.items():
                    setattr(existing, field, value)
                
                db.add(existing)
                successful += 1
            else:
                # Create new
                result_data = ConstituencyResultCreate(
                    constituency_id=constituency.id,
                    election_year=election_year,
                    election_type=election_type,
                    total_votes=int(row["total_votes"]),
                    valid_votes=int(row["valid_votes"]),
                    rejected_votes=int(row["rejected_votes"]),
                    turnout_percentage=float(row["turnout_percentage"]),
                    winning_candidate_id=winning_candidate.id if winning_candidate else None,
                    winning_party_id=winning_party.id if winning_party else None,
                    margin_votes=int(row["margin_votes"]) if "margin_votes" in row and pd.notna(row["margin_votes"]) else None,
                    margin_percentage=float(row["margin_percentage"]) if "margin_percentage" in row and pd.notna(row["margin_percentage"]) else None,
                    is_official=bool(row["is_official"]) if "is_official" in row else False
                )
                
                # Validate vote totals
                if result_data.valid_votes + result_data.rejected_votes != result_data.total_votes:
                    errors.append({
                        "row": idx + 2,
                        "error": f"Valid votes ({result_data.valid_votes}) + Rejected votes ({result_data.rejected_votes}) must equal Total votes ({result_data.total_votes})"
                    })
                    failed += 1
                    continue
                
                crud_constituency_result.create(db, obj_in=result_data)
                successful += 1
                
        except Exception as e:
            failed += 1
            errors.append({
                "row": idx + 2,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "total_rows": len(df),
        "successful_rows": successful,
        "failed_rows": failed,
        "errors": errors
    }
