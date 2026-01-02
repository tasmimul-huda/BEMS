from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
from app.models.election import (
    VoterDemographics, PollingCenter, PollingCenterResult,
    ConstituencyResult, ImportLog
)
from app.schemas.election import (
    VoterDemographicsCreate, VoterDemographicsUpdate,
    PollingCenterCreate, PollingCenterUpdate,
    PollingCenterResultCreate, PollingCenterResultUpdate,
    ConstituencyResultCreate, ConstituencyResultUpdate
)
from fastapi import HTTPException, status


class CRUDVoterDemographics:
    def get(self, db: Session, demographics_id: int) -> Optional[VoterDemographics]:
        return db.query(VoterDemographics).filter(VoterDemographics.id == demographics_id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[VoterDemographics]:
        return db.query(VoterDemographics).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: VoterDemographicsCreate) -> VoterDemographics:
        # Check if demographics already exists for constituency and year
        existing = db.query(VoterDemographics).filter(
            VoterDemographics.constituency_id == obj_in.constituency_id,
            VoterDemographics.election_year == obj_in.election_year
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voter demographics already exists for this constituency and election year"
            )
        
        db_obj = VoterDemographics(**obj_in.model_dump())
        db_obj.last_updated = db_obj.created_at
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: VoterDemographics, obj_in: VoterDemographicsUpdate
    ) -> VoterDemographics:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if constituency_id or election_year is being updated
        if 'constituency_id' in update_data or 'election_year' in update_data:
            existing = db.query(VoterDemographics).filter(
                VoterDemographics.constituency_id == update_data.get('constituency_id', db_obj.constituency_id),
                VoterDemographics.election_year == update_data.get('election_year', db_obj.election_year),
                VoterDemographics.id != db_obj.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Voter demographics already exists for this constituency and election year"
                )
        
        # Update last_updated timestamp
        from datetime import datetime
        update_data['last_updated'] = datetime.utcnow()
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, demographics_id: int) -> VoterDemographics:
        db_obj = self.get(db, demographics_id=demographics_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Voter demographics not found"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDPollingCenter:
    def get(self, db: Session, center_id: int) -> Optional[PollingCenter]:
        return db.query(PollingCenter).filter(PollingCenter.id == center_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[PollingCenter]:
        return db.query(PollingCenter).filter(PollingCenter.code == code).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[PollingCenter]:
        return db.query(PollingCenter).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: PollingCenterCreate) -> PollingCenter:
        # Check if polling center with same code exists
        existing = self.get_by_code(db, code=obj_in.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Polling center with this code already exists"
            )
        
        db_obj = PollingCenter(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: PollingCenter, obj_in: PollingCenterUpdate
    ) -> PollingCenter:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if code is being updated
        if 'code' in update_data:
            existing = db.query(PollingCenter).filter(
                PollingCenter.code == update_data['code'],
                PollingCenter.id != db_obj.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Polling center with this code already exists"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, center_id: int) -> PollingCenter:
        db_obj = self.get(db, center_id=center_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Polling center not found"
            )
        
        # Check if polling center has results
        if db_obj.results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete polling center with associated results"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDPollingCenterResult:
    def get(self, db: Session, result_id: int) -> Optional[PollingCenterResult]:
        return db.query(PollingCenterResult).filter(PollingCenterResult.id == result_id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[PollingCenterResult]:
        return db.query(PollingCenterResult).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: PollingCenterResultCreate) -> PollingCenterResult:
        # Check if result already exists for this center and candidate
        existing = db.query(PollingCenterResult).filter(
            PollingCenterResult.polling_center_id == obj_in.polling_center_id,
            PollingCenterResult.candidate_id == obj_in.candidate_id,
            PollingCenterResult.election_year == obj_in.election_year
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Result already exists for this polling center and candidate"
            )
        
        db_obj = PollingCenterResult(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: PollingCenterResult, obj_in: PollingCenterResultUpdate
    ) -> PollingCenterResult:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, result_id: int) -> PollingCenterResult:
        db_obj = self.get(db, result_id=result_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Polling center result not found"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDConstituencyResult:
    def get(self, db: Session, result_id: int) -> Optional[ConstituencyResult]:
        return db.query(ConstituencyResult).filter(ConstituencyResult.id == result_id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ConstituencyResult]:
        return db.query(ConstituencyResult).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: ConstituencyResultCreate) -> ConstituencyResult:
        # Check if result already exists for constituency and year
        existing = db.query(ConstituencyResult).filter(
            ConstituencyResult.constituency_id == obj_in.constituency_id,
            ConstituencyResult.election_year == obj_in.election_year,
            ConstituencyResult.election_type == obj_in.election_type
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Result already exists for this constituency and election year"
            )
        
        db_obj = ConstituencyResult(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: ConstituencyResult, obj_in: ConstituencyResultUpdate
    ) -> ConstituencyResult:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if constituency_id or election_year is being updated
        if 'constituency_id' in update_data or 'election_year' in update_data or 'election_type' in update_data:
            existing = db.query(ConstituencyResult).filter(
                ConstituencyResult.constituency_id == update_data.get('constituency_id', db_obj.constituency_id),
                ConstituencyResult.election_year == update_data.get('election_year', db_obj.election_year),
                ConstituencyResult.election_type == update_data.get('election_type', db_obj.election_type),
                ConstituencyResult.id != db_obj.id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Result already exists for this constituency and election year"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, result_id: int) -> ConstituencyResult:
        db_obj = self.get(db, result_id=result_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constituency result not found"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDImportLog:
    def get(self, db: Session, log_id: int) -> Optional[ImportLog]:
        return db.query(ImportLog).filter(ImportLog.id == log_id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ImportLog]:
        return db.query(ImportLog).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: dict) -> ImportLog:
        db_obj = ImportLog(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


crud_voter_demographics = CRUDVoterDemographics()
crud_polling_center = CRUDPollingCenter()
crud_polling_result = CRUDPollingCenterResult()
crud_constituency_result = CRUDConstituencyResult()
crud_import_log = CRUDImportLog()