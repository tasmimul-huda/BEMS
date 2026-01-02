from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, or_
import math

from app.database import get_db
from app.dependencies import require_data_entry_or_above, require_viewer_or_above
from app.crud.candidate import crud_candidate, crud_party
from app.schemas.candidate import (
    CandidateCreate, CandidateUpdate, CandidateInDB, CandidateWithResults,
    PartyCreate, PartyUpdate, PartyInDB
)
from app.models.candidate import Candidate, Party
from app.models.geography import Constituency

router = APIRouter(prefix="/candidates", tags=["candidates"])


# Party Endpoints
@router.post("/parties/", response_model=PartyInDB, status_code=status.HTTP_201_CREATED)
def create_party(
    party: PartyCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Create a new political party"""
    return crud_party.create(db=db, obj_in=party)


@router.get("/parties/", response_model=List[PartyInDB])
def read_parties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    is_registered: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get all political parties"""
    query = db.query(Party)
    
    if search:
        query = query.filter(
            or_(
                Party.name.ilike(f"%{search}%"),
                Party.acronym.ilike(f"%{search}%"),
                Party.symbol_name.ilike(f"%{search}%")
            )
        )
    
    if is_registered is not None:
        query = query.filter(Party.is_registered == is_registered)
    
    return query.order_by(Party.name).offset(skip).limit(limit).all()


@router.get("/parties/{party_id}", response_model=PartyInDB)
def read_party(
    party_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get a specific political party"""
    party = crud_party.get(db, party_id=party_id)
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found"
        )
    return party


@router.put("/parties/{party_id}", response_model=PartyInDB)
def update_party(
    party_id: int,
    party_update: PartyUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Update a political party"""
    party = crud_party.get(db, party_id=party_id)
    if not party:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party not found"
        )
    return crud_party.update(db=db, db_obj=party, obj_in=party_update)


@router.delete("/parties/{party_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_party(
    party_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Delete a political party"""
    crud_party.delete(db=db, party_id=party_id)
    return None


@router.get("/parties/{party_id}/candidates")
def get_party_candidates(
    party_id: int,
    election_year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get all candidates for a party"""
    query = db.query(Candidate).filter(Candidate.party_id == party_id)
    
    if election_year:
        query = query.filter(Candidate.election_year == election_year)
    
    candidates = query.options(
        joinedload(Candidate.constituency).joinedload(Constituency.district)
    ).order_by(Candidate.election_year.desc(), Candidate.full_name).offset(skip).limit(limit).all()
    
    total = query.count()
    
    return {
        "party_id": party_id,
        "total_candidates": total,
        "candidates": candidates,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if limit > 0 else 1
        }
    }


# Candidate Endpoints
@router.post("/", response_model=CandidateInDB, status_code=status.HTTP_201_CREATED)
def create_candidate(
    candidate: CandidateCreate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Create a new candidate"""
    return crud_candidate.create(db=db, obj_in=candidate)


@router.get("/", response_model=List[CandidateInDB])
def read_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    constituency_id: Optional[int] = Query(None),
    party_id: Optional[int] = Query(None),
    election_year: Optional[int] = Query(None),
    election_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(True),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get all candidates with filters"""
    query = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.constituency).joinedload(Constituency.district)
    )
    
    if constituency_id:
        query = query.filter(Candidate.constituency_id == constituency_id)
    if party_id:
        query = query.filter(Candidate.party_id == party_id)
    if election_year:
        query = query.filter(Candidate.election_year == election_year)
    if election_type:
        query = query.filter(Candidate.election_type == election_type)
    if is_active is not None:
        query = query.filter(Candidate.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                Candidate.full_name.ilike(f"%{search}%"),
                Candidate.bengali_name.ilike(f"%{search}%"),
                Candidate.education.ilike(f"%{search}%"),
                Candidate.profession.ilike(f"%{search}%")
            )
        )
    
    return query.order_by(
        desc(Candidate.election_year),
        Candidate.constituency_id,
        Candidate.full_name
    ).offset(skip).limit(limit).all()


@router.get("/{candidate_id}", response_model=CandidateWithResults)
def read_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get a specific candidate with results"""
    candidate = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.constituency).joinedload(Constituency.district),
        joinedload(Candidate.polling_results)
    ).filter(Candidate.id == candidate_id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    
    # Calculate total votes
    total_votes = sum([r.votes_received for r in candidate.polling_results]) if candidate.polling_results else 0
    
    # Convert to dict and add extra fields
    candidate_dict = {**candidate.__dict__}
    candidate_dict["total_votes"] = total_votes
    candidate_dict["vote_percentage"] = None  # Can be calculated later
    
    return candidate_dict


@router.put("/{candidate_id}", response_model=CandidateInDB)
def update_candidate(
    candidate_id: int,
    candidate_update: CandidateUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Update a candidate"""
    candidate = crud_candidate.get(db, candidate_id=candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found"
        )
    return crud_candidate.update(db=db, db_obj=candidate, obj_in=candidate_update)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_data_entry_or_above)
):
    """Delete a candidate"""
    crud_candidate.delete(db=db, candidate_id=candidate_id)
    return None


@router.get("/constituency/{constituency_id}")
def get_constituency_candidates(
    constituency_id: int,
    election_year: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get all candidates for a specific constituency in an election year"""
    candidates = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.polling_results)
    ).filter(
        Candidate.constituency_id == constituency_id,
        Candidate.election_year == election_year,
        Candidate.is_active == True
    ).all()
    
    # Calculate vote totals
    candidates_with_votes = []
    for candidate in candidates:
        total_votes = sum([r.votes_received for r in candidate.polling_results]) if candidate.polling_results else 0
        candidate_dict = {**candidate.__dict__}
        candidate_dict["total_votes"] = total_votes
        candidates_with_votes.append(candidate_dict)
    
    # Sort by votes (descending)
    candidates_with_votes.sort(key=lambda x: x["total_votes"], reverse=True)
    
    return {
        "constituency_id": constituency_id,
        "election_year": election_year,
        "candidates": candidates_with_votes,
        "total_candidates": len(candidates_with_votes)
    }


@router.get("/search/advanced")
def advanced_search(
    name: Optional[str] = Query(None),
    party_name: Optional[str] = Query(None),
    constituency_number: Optional[str] = Query(None),
    education: Optional[str] = Query(None),
    profession: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None, ge=21),
    max_age: Optional[int] = Query(None, le=150),
    election_year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Advanced candidate search"""
    from app.models.geography import Constituency
    
    query = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.constituency).joinedload(Constituency.district)
    )
    
    # Apply filters
    if name:
        query = query.filter(
            or_(
                Candidate.full_name.ilike(f"%{name}%"),
                Candidate.bengali_name.ilike(f"%{name}%")
            )
        )
    if party_name:
        query = query.join(Candidate.party).filter(Party.name.ilike(f"%{party_name}%"))
    if constituency_number:
        query = query.join(Candidate.constituency).filter(
            Constituency.number.ilike(f"%{constituency_number}%")
        )
    if education:
        query = query.filter(Candidate.education.ilike(f"%{education}%"))
    if profession:
        query = query.filter(Candidate.profession.ilike(f"%{profession}%"))
    if min_age:
        query = query.filter(Candidate.age >= min_age)
    if max_age:
        query = query.filter(Candidate.age <= max_age)
    if election_year:
        query = query.filter(Candidate.election_year == election_year)
    
    # Get total count
    total = query.count()
    
    # Get results
    results = query.order_by(Candidate.full_name).offset(skip).limit(limit).all()
    
    return {
        "results": results,
        "total": total,
        "pagination": {
            "skip": skip,
            "limit": limit,
            "pages": math.ceil(total / limit) if limit > 0 else 1
        }
    }


@router.get("/stats/party-wise")
def get_party_wise_stats(
    election_year: int = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Get party-wise candidate statistics for an election year"""
    from app.models.election import PollingCenterResult
    
    # Get all parties with candidate counts
    party_stats = db.query(
        Party.id,
        Party.name,
        Party.acronym,
        Party.symbol_name,
        Party.color_code,
        func.count(Candidate.id).label('candidate_count')
    ).join(
        Candidate, Candidate.party_id == Party.id
    ).filter(
        Candidate.election_year == election_year,
        Candidate.is_active == True
    ).group_by(
        Party.id, Party.name, Party.acronym, Party.symbol_name, Party.color_code
    ).order_by(
        desc('candidate_count')
    ).all()
    
    # Get total votes per party
    party_votes = []
    for party in party_stats:
        # Get all candidates for this party
        candidates = db.query(Candidate.id).filter(
            Candidate.party_id == party.id,
            Candidate.election_year == election_year
        ).all()
        
        candidate_ids = [c.id for c in candidates]
        
        # Get total votes for these candidates
        if candidate_ids:
            total_votes = db.query(func.sum(PollingCenterResult.votes_received)).filter(
                PollingCenterResult.candidate_id.in_(candidate_ids),
                PollingCenterResult.election_year == election_year
            ).scalar() or 0
        else:
            total_votes = 0
        
        party_votes.append({
            "party_id": party.id,
            "party_name": party.name,
            "acronym": party.acronym,
            "symbol_name": party.symbol_name,
            "color_code": party.color_code,
            "candidate_count": party.candidate_count,
            "total_votes": total_votes
        })
    
    return {
        "election_year": election_year,
        "party_stats": party_votes,
        "total_parties": len(party_votes),
        "total_candidates": sum([p["candidate_count"] for p in party_votes])
    }


@router.get("/compare/{candidate_id1}/{candidate_id2}")
def compare_candidates(
    candidate_id1: int,
    candidate_id2: int,
    db: Session = Depends(get_db),
    current_user = Depends(require_viewer_or_above)
):
    """Compare two candidates side by side"""
    from app.models.election import PollingCenterResult
    
    # Get candidates with details
    candidate1 = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.constituency)
    ).filter(Candidate.id == candidate_id1).first()
    
    candidate2 = db.query(Candidate).options(
        joinedload(Candidate.party),
        joinedload(Candidate.constituency)
    ).filter(Candidate.id == candidate_id2).first()
    
    if not candidate1 or not candidate2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both candidates not found"
        )
    
    # Get vote totals
    votes1 = db.query(func.sum(PollingCenterResult.votes_received)).filter(
        PollingCenterResult.candidate_id == candidate_id1
    ).scalar() or 0
    
    votes2 = db.query(func.sum(PollingCenterResult.votes_received)).filter(
        PollingCenterResult.candidate_id == candidate_id2
    ).scalar() or 0
    
    comparison = {
        "candidate1": {
            "id": candidate1.id,
            "name": candidate1.full_name,
            "bengali_name": candidate1.bengali_name,
            "age": candidate1.age,
            "education": candidate1.education,
            "profession": candidate1.profession,
            "party": candidate1.party.name if candidate1.party else None,
            "constituency": candidate1.constituency.name if candidate1.constituency else None,
            "election_year": candidate1.election_year,
            "total_votes": votes1,
            "photo_url": candidate1.photo_url
        },
        "candidate2": {
            "id": candidate2.id,
            "name": candidate2.full_name,
            "bengali_name": candidate2.bengali_name,
            "age": candidate2.age,
            "education": candidate2.education,
            "profession": candidate2.profession,
            "party": candidate2.party.name if candidate2.party else None,
            "constituency": candidate2.constituency.name if candidate2.constituency else None,
            "election_year": candidate2.election_year,
            "total_votes": votes2,
            "photo_url": candidate2.photo_url
        },
        "differences": {
            "age_difference": abs((candidate1.age or 0) - (candidate2.age or 0)),
            "vote_difference": abs(votes1 - votes2),
            "same_constituency": candidate1.constituency_id == candidate2.constituency_id,
            "same_election_year": candidate1.election_year == candidate2.election_year
        }
    }
    
    return comparison