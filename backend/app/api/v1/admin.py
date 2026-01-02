from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import pandas as pd
import io
from datetime import datetime, timedelta

from app.database import get_db
from app.dependencies import (
    get_current_user, require_super_admin, 
    require_data_entry_or_above, require_viewer_or_above
)
from app.crud.user import crud_user
from app.crud.candidate import crud_candidate, crud_party
from app.crud.election import (
    crud_voter_demographics, crud_polling_center,
    crud_polling_result, crud_constituency_result,
    crud_import_log
)
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserInDB
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateInDB,
    PartyCreate, PartyUpdate, PartyInDB
)
from app.schemas.election import (
    VoterDemographicsCreate, VoterDemographicsUpdate, VoterDemographicsInDB,
    PollingCenterCreate, PollingCenterUpdate, PollingCenterInDB,
    PollingCenterResultCreate, PollingCenterResultUpdate, PollingCenterResultInDB,
    ConstituencyResultCreate, ConstituencyResultUpdate, ConstituencyResultInDB
)
from app.models.user import UserRole
from app.models.election import ImportLog
from app.utils.csv_import import (
    validate_candidate_csv, import_candidate_data,
    validate_party_csv, import_party_data,
    validate_polling_center_csv, import_polling_center_data,
    validate_polling_result_csv, import_polling_result_data,
    validate_voter_demographics_csv, import_voter_demographics_data,
    validate_constituency_result_csv, import_constituency_result_data
)

router = APIRouter(prefix="/admin", tags=["admin"])


# User Management Endpoints (Super Admin Only)
@router.post("/users/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Create a new admin user"""
    return crud_user.create(db=db, obj_in=user_in)


@router.get("/users/", response_model=List[UserResponse])
def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Get all admin users"""
    query = db.query(crud_user.model)
    
    if role:
        query = query.filter(crud_user.model.role == role)
    if is_active is not None:
        query = query.filter(crud_user.model.is_active == is_active)
    if search:
        query = query.filter(
            crud_user.model.email.ilike(f"%{search}%") |
            crud_user.model.full_name.ilike(f"%{search}%")
        )
    
    users = query.order_by(crud_user.model.created_at.desc()).offset(skip).limit(limit).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Get a specific admin user"""
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Update an admin user"""
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent self-demotion
    if user_id == current_user.id and user_update.role and user_update.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role from super admin"
        )
    
    return crud_user.update(db=db, db_obj=user, obj_in=user_update)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Delete an admin user"""
    # Prevent self-deletion
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    crud_user.delete(db=db, user_id=user_id)
    return None


@router.put("/users/{user_id}/toggle-active", response_model=UserResponse)
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Toggle user active status"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user = crud_user.get(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    return user


# Import Logs
@router.get("/import-logs/")
def get_import_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    import_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Get import logs"""
    query = db.query(ImportLog).join(ImportLog.user)
    
    if import_type:
        query = query.filter(ImportLog.import_type == import_type)
    if status:
        query = query.filter(ImportLog.status == status)
    if user_id:
        query = query.filter(ImportLog.user_id == user_id)
    if start_date:
        query = query.filter(ImportLog.created_at >= start_date)
    if end_date:
        query = query.filter(ImportLog.created_at <= end_date)
    
    total = query.count()
    logs = query.order_by(desc(ImportLog.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "logs": logs,
        "skip": skip,
        "limit": limit
    }


@router.get("/import-logs/{log_id}")
def get_import_log(
    log_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Get specific import log"""
    log = db.query(ImportLog).filter(ImportLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Import log not found"
        )
    return log


# System Statistics
@router.get("/stats/")
def get_system_stats(
    db: Session = Depends(get_db),
    current_user = Depends(require_super_admin)
):
    """Get system statistics"""
    from app.models.geography import Division, District, Constituency
    from app.models.candidate import Candidate, Party
    from app.models.election import (
        VoterDemographics, PollingCenter,
        PollingCenterResult, ConstituencyResult
    )
    from app.models.user import AdminUser
    
    stats = {
        "geography": {
            "divisions": db.query(func.count(Division.id)).scalar() or 0,
            "districts": db.query(func.count(District.id)).scalar() or 0,
            "constituencies": db.query(func.count(Constituency.id)).scalar() or 0,
            "active_constituencies": db.query(func.count(Constituency.id))
                .filter(Constituency.is_active == True).scalar() or 0,
        },
        "candidates": {
            "parties": db.query(func.count(Party.id)).scalar() or 0,
            "candidates": db.query(func.count(Candidate.id)).scalar() or 0,
            "active_candidates": db.query(func.count(Candidate.id))
                .filter(Candidate.is_active == True).scalar() or 0,
        },
        "election": {
            "polling_centers": db.query(func.count(PollingCenter.id)).scalar() or 0,
            "voter_demographics": db.query(func.count(VoterDemographics.id)).scalar() or 0,
            "polling_results": db.query(func.count(PollingCenterResult.id)).scalar() or 0,
            "constituency_results": db.query(func.count(ConstituencyResult.id)).scalar() or 0,
        },
        "users": {
            "total": db.query(func.count(AdminUser.id)).scalar() or 0,
            "super_admins": db.query(func.count(AdminUser.id))
                .filter(AdminUser.role == UserRole.SUPER_ADMIN).scalar() or 0,
            "data_entry": db.query(func.count(AdminUser.id))
                .filter(AdminUser.role == UserRole.DATA_ENTRY).scalar() or 0,
            "viewers": db.query(func.count(AdminUser.id))
                .filter(AdminUser.role == UserRole.VIEWER).scalar() or 0,
            "active": db.query(func.count(AdminUser.id))
                .filter(AdminUser.is_active == True).scalar() or 0,
        },
        "imports": {
            "total": db.query(func.count(ImportLog.id)).scalar() or 0,
            "successful": db.query(func.count(ImportLog.id))
                .filter(ImportLog.status == "completed").scalar() or 0,
            "failed": db.query(func.count(ImportLog.id))
                .filter(ImportLog.status == "failed").scalar() or 0,
        }
    }
    
    return stats


# CSV Import Templates
@router.get("/templates/{template_type}")
def get_csv_template(
    template_type: str,
    current_user = Depends(require_data_entry_or_above)
):
    """Get CSV template for data import"""
    templates = {
        "constituency": {
            "columns": ["division_name", "district_name", "number", "name", "area_description", "total_voters", "is_active"],
            "sample": [
                ["Dhaka", "Dhaka", "1", "Dhaka-1", "Area description here", "350000", "true"],
                ["Dhaka", "Dhaka", "2", "Dhaka-2", "Area description here", "320000", "true"]
            ],
            "description": "Import constituencies with division and district names"
        },
        "candidate": {
            "columns": ["full_name", "bengali_name", "party_name", "constituency_number", "election_year", 
                       "election_type", "age", "education", "profession", "candidate_number"],
            "sample": [
                ["John Doe", "জন ডো", "Awami League", "1", "2024", "National", "45", "MA, University of Dhaka", "Businessman", "1"],
                ["Jane Smith", "জেন স্মিথ", "Bangladesh Nationalist Party", "1", "2024", "National", "52", "MSc, BUET", "Engineer", "2"]
            ],
            "description": "Import candidates with party and constituency details"
        },
        "party": {
            "columns": ["name", "acronym", "symbol_name", "color_code", "is_registered"],
            "sample": [
                ["Awami League", "AL", "Boat", "#006A4E", "true"],
                ["Bangladesh Nationalist Party", "BNP", "Sheaf of Paddy", "#3C8D2F", "true"]
            ],
            "description": "Import political parties"
        },
        "polling_center": {
            "columns": ["code", "name", "constituency_number", "location", "latitude", "longitude", "total_voters"],
            "sample": [
                ["PC-001", "Dhaka College Center", "1", "Dhaka College, Dhaka", "23.7272", "90.3944", "3000"],
                ["PC-002", "Bangla Academy Center", "1", "Bangla Academy, Dhaka", "23.7333", "90.3944", "2500"]
            ],
            "description": "Import polling centers with constituency numbers"
        },
        "polling_result": {
            "columns": ["polling_center_code", "candidate_name", "constituency_number", "election_year", "votes_received"],
            "sample": [
                ["PC-001", "John Doe", "1", "2024", "1500"],
                ["PC-001", "Jane Smith", "1", "2024", "1200"]
            ],
            "description": "Import polling center results"
        },
        "voter_demographics": {
            "columns": ["constituency_number", "election_year", "total_voters", "male_voters", "female_voters", 
                       "other_voters", "age_18_25", "age_26_35", "age_36_45", "age_46_55", "age_56_65", "age_66_plus"],
            "sample": [
                ["1", "2024", "350000", "180000", "170000", "0", "50000", "80000", "70000", "60000", "50000", "40000"]
            ],
            "description": "Import voter demographics"
        }
    }
    
    if template_type not in templates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template type not found"
        )
    
    return templates[template_type]

from fastapi import UploadFile, File
# Bulk CSV Import Endpoint
@router.post("/import/{import_type}")
async def bulk_import(
    import_type: str,
    file: UploadFile = File(...),
    dry_run: bool = Query(False),
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Bulk import data from CSV"""
    
    import_handlers = {
        "candidate": (validate_candidate_csv, import_candidate_data),
        "party": (validate_party_csv, import_party_data),
        "polling_center": (validate_polling_center_csv, import_polling_center_data),
        "polling_result": (validate_polling_result_csv, import_polling_result_data),
        "voter_demographics": (validate_voter_demographics_csv, import_voter_demographics_data),
        "constituency_result": (validate_constituency_result_csv, import_constituency_result_data)
    }
    
    if import_type not in import_handlers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported import type: {import_type}"
        )
    
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
        
        # Get validator and importer
        validator, importer = import_handlers[import_type]
        
        # Validate CSV
        errors = validator(df)
        
        if dry_run:
            return {
                "total_rows": len(df),
                "successful_rows": len(df) - len(errors),
                "failed_rows": len(errors),
                "errors": errors,
                "preview_data": df.head(10).to_dict('records')
            }
        
        if errors:
            # Create import log for failed import
            import_log = ImportLog(
                import_type=import_type,
                file_name=file.filename,
                total_rows=len(df),
                successful_rows=0,
                failed_rows=len(df),
                errors=errors,
                user_id=current_user.id,
                status="failed"
            )
            db.add(import_log)
            db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": errors}
            )
        
        # Import data
        result = importer(db, df, current_user.id)
        
        # Create import log
        import_log = ImportLog(
            import_type=import_type,
            file_name=file.filename,
            total_rows=result["total_rows"],
            successful_rows=result["successful_rows"],
            failed_rows=result["failed_rows"],
            errors=result["errors"],
            user_id=current_user.id,
            status="completed"
        )
        db.add(import_log)
        db.commit()
        
        return result
        
    except pd.errors.EmptyDataError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file is empty"
        )
    except pd.errors.ParserError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV format"
        )
    except Exception as e:
        # Log the error
        import_log = ImportLog(
            import_type=import_type,
            file_name=file.filename,
            total_rows=0,
            successful_rows=0,
            failed_rows=0,
            errors=[{"error": str(e)}],
            user_id=current_user.id,
            status="failed"
        )
        db.add(import_log)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )
from app.models.candidate import Candidate
from app.models.election import ConstituencyResult

# Data Export Endpoint
@router.get("/export/{data_type}")
def export_data(
    data_type: str,
    format: str = Query("csv", pattern="^(csv|json)$"),
    election_year: Optional[int] = Query(None),
    constituency_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Export data in CSV or JSON format"""
    
    if data_type == "candidates":
        query = db.query(Candidate)
        if election_year:
            query = query.filter(Candidate.election_year == election_year)
        if constituency_id:
            query = query.filter(Candidate.constituency_id == constituency_id)
        
        data = query.all()
        
        if format == "csv":
            # Convert to CSV
            df = pd.DataFrame([{
                "id": c.id,
                "full_name": c.full_name,
                "party": c.party.name if c.party else "",
                "constituency": f"{c.constituency.number}: {c.constituency.name}" if c.constituency else "",
                "election_year": c.election_year,
                "votes_received": sum([r.votes_received for r in c.polling_results]) if c.polling_results else 0
            } for c in data])
            
            csv_data = df.to_csv(index=False)
            return {
                "filename": f"candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "data": csv_data,
                "format": "csv"
            }
        
        else:  # json
            return {
                "filename": f"candidates_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "data": [{
                    "id": c.id,
                    "full_name": c.full_name,
                    "party": c.party.name if c.party else "",
                    "constituency": f"{c.constituency.number}: {c.constituency.name}" if c.constituency else "",
                    "election_year": c.election_year,
                    "votes_received": sum([r.votes_received for r in c.polling_results]) if c.polling_results else 0
                } for c in data],
                "format": "json"
            }
    
    elif data_type == "results":
        query = db.query(ConstituencyResult)
        if election_year:
            query = query.filter(ConstituencyResult.election_year == election_year)
        if constituency_id:
            query = query.filter(ConstituencyResult.constituency_id == constituency_id)
        
        data = query.all()
        
        if format == "csv":
            df = pd.DataFrame([{
                "constituency_id": r.constituency_id,
                "constituency_name": r.constituency.name if r.constituency else "",
                "election_year": r.election_year,
                "total_votes": r.total_votes,
                "valid_votes": r.valid_votes,
                "rejected_votes": r.rejected_votes,
                "turnout_percentage": r.turnout_percentage,
                "winning_candidate": r.winning_candidate.full_name if r.winning_candidate else "",
                "winning_party": r.winning_party.name if r.winning_party else "",
                "margin_votes": r.margin_votes,
                "is_official": r.is_official
            } for r in data])
            
            csv_data = df.to_csv(index=False)
            return {
                "filename": f"results_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "data": csv_data,
                "format": "csv"
            }
        
        else:
            return {
                "filename": f"results_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "data": [{
                    "constituency_id": r.constituency_id,
                    "constituency_name": r.constituency.name if r.constituency else "",
                    "election_year": r.election_year,
                    "total_votes": r.total_votes,
                    "valid_votes": r.valid_votes,
                    "rejected_votes": r.rejected_votes,
                    "turnout_percentage": r.turnout_percentage,
                    "winning_candidate": r.winning_candidate.full_name if r.winning_candidate else "",
                    "winning_party": r.winning_party.name if r.winning_party else "",
                    "margin_votes": r.margin_votes,
                    "is_official": r.is_official
                } for r in data],
                "format": "json"
            }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported export type: {data_type}"
        )
from app.models.user import AdminUser

# Dashboard data for admin
@router.get("/dashboard")
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Get admin dashboard data"""
    
    # Recent imports
    recent_imports = db.query(ImportLog).order_by(
        desc(ImportLog.created_at)
    ).limit(10).all()
    
    # Recent user activity
    recent_users = db.query(AdminUser).order_by(
        desc(AdminUser.last_login)
    ).limit(5).all()
    
    # Election stats
    
    latest_election = db.query(ConstituencyResult).order_by(
        desc(ConstituencyResult.election_year)
    ).first()
    
    if latest_election:
        election_stats = {
            "year": latest_election.election_year,
            "total_constituencies": db.query(func.count(ConstituencyResult.id))
                .filter(ConstituencyResult.election_year == latest_election.election_year)
                .scalar() or 0,
            "results_declared": db.query(func.count(ConstituencyResult.id))
                .filter(
                    ConstituencyResult.election_year == latest_election.election_year,
                    ConstituencyResult.is_official == True
                ).scalar() or 0,
            "total_votes": db.query(func.sum(ConstituencyResult.total_votes))
                .filter(ConstituencyResult.election_year == latest_election.election_year)
                .scalar() or 0
        }
    else:
        election_stats = None
    
    # Pending tasks (imports with errors)
    pending_imports = db.query(ImportLog).filter(
        ImportLog.status.in_(["pending", "processing"])
    ).count()
    
    return {
        "recent_imports": recent_imports,
        "recent_user_activity": recent_users,
        "election_stats": election_stats,
        "pending_tasks": pending_imports,
        "user_role": current_user.role.value,
        "user_name": current_user.full_name
    }