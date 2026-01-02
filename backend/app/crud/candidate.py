from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.candidate import Candidate, Party
from app.schemas.candidate import CandidateCreate, CandidateUpdate, PartyCreate, PartyUpdate
from fastapi import HTTPException, status


class CRUDParty:
    def get(self, db: Session, party_id: int) -> Optional[Party]:
        return db.query(Party).filter(Party.id == party_id).first()
    
    def get_by_name(self, db: Session, name: str) -> Optional[Party]:
        return db.query(Party).filter(Party.name == name).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Party]:
        return db.query(Party).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: PartyCreate) -> Party:
        # Check if party with same name exists
        existing = self.get_by_name(db, name=obj_in.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Party with this name already exists"
            )
        
        db_obj = Party(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Party, obj_in: PartyUpdate
    ) -> Party:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if name is being updated
        if 'name' in update_data:
            existing = db.query(Party).filter(
                Party.name == update_data['name'],
                Party.id != db_obj.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Party with this name already exists"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, party_id: int) -> Party:
        db_obj = self.get(db, party_id=party_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Party not found"
            )
        
        # Check if party has candidates
        if db_obj.candidates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete party with associated candidates"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDCandidate:
    def get(self, db: Session, candidate_id: int) -> Optional[Candidate]:
        return db.query(Candidate).filter(Candidate.id == candidate_id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[Candidate]:
        return db.query(Candidate).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: CandidateCreate) -> Candidate:
        # Check if candidate already exists for same constituency and election
        existing = db.query(Candidate).filter(
            Candidate.full_name == obj_in.full_name,
            Candidate.constituency_id == obj_in.constituency_id,
            Candidate.election_year == obj_in.election_year
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Candidate already exists for this constituency and election year"
            )
        
        db_obj = Candidate(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Candidate, obj_in: CandidateUpdate
    ) -> Candidate:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if key fields are being updated
        if 'full_name' in update_data or 'constituency_id' in update_data or 'election_year' in update_data:
            existing = db.query(Candidate).filter(
                Candidate.full_name == update_data.get('full_name', db_obj.full_name),
                Candidate.constituency_id == update_data.get('constituency_id', db_obj.constituency_id),
                Candidate.election_year == update_data.get('election_year', db_obj.election_year),
                Candidate.id != db_obj.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Candidate already exists for this constituency and election year"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, candidate_id: int) -> Candidate:
        db_obj = self.get(db, candidate_id=candidate_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Candidate not found"
            )
        
        # Check if candidate has results
        if db_obj.polling_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete candidate with associated election results"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


crud_party = CRUDParty()
crud_candidate = CRUDCandidate()