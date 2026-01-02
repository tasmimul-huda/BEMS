from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List, Dict, Any
from app.models.geography import Division, District, Constituency
from app.schemas.geography import (
    DivisionCreate, DivisionUpdate,
    DistrictCreate, DistrictUpdate,
    ConstituencyCreate, ConstituencyUpdate
)
from fastapi import HTTPException, status


class CRUDDivision:
    def get(self, db: Session, division_id: int) -> Optional[Division]:
        return db.query(Division).filter(Division.id == division_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[Division]:
        return db.query(Division).filter(Division.code == code).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100,
        search: Optional[str] = None
    ) -> List[Division]:
        query = db.query(Division)
        if search:
            query = query.filter(
                or_(
                    Division.name.ilike(f"%{search}%"),
                    Division.bengali_name.ilike(f"%{search}%"),
                    Division.code.ilike(f"%{search}%")
                )
            )
        return query.order_by(Division.name).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: DivisionCreate) -> Division:
        # Check if division with same code or name exists
        existing = db.query(Division).filter(
            or_(
                Division.code == obj_in.code,
                Division.name == obj_in.name
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Division with this code or name already exists"
            )
        
        db_obj = Division(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Division, obj_in: DivisionUpdate
    ) -> Division:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if code or name is being updated
        if 'code' in update_data or 'name' in update_data:
            filters = []
            if 'code' in update_data:
                filters.append(Division.code == update_data['code'])
            if 'name' in update_data:
                filters.append(Division.name == update_data['name'])
            
            existing = db.query(Division).filter(
                and_(*filters, Division.id != db_obj.id)
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Division with this code or name already exists"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, division_id: int) -> Division:
        db_obj = self.get(db, division_id=division_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Division not found"
            )
        
        # Check if division has districts
        if db_obj.districts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete division with associated districts"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDDistrict:
    def get(self, db: Session, district_id: int) -> Optional[District]:
        return db.query(District).filter(District.id == district_id).first()
    
    def get_by_code(self, db: Session, code: str) -> Optional[District]:
        return db.query(District).filter(District.code == code).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100,
        division_id: Optional[int] = None, search: Optional[str] = None
    ) -> List[District]:
        query = db.query(District)
        
        if division_id:
            query = query.filter(District.division_id == division_id)
        
        if search:
            query = query.filter(
                or_(
                    District.name.ilike(f"%{search}%"),
                    District.bengali_name.ilike(f"%{search}%"),
                    District.code.ilike(f"%{search}%")
                )
            )
        
        return query.order_by(District.name).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: DistrictCreate) -> District:
        # Check if district with same code exists in same division
        existing = db.query(District).filter(
            and_(
                District.code == obj_in.code,
                District.division_id == obj_in.division_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="District with this code already exists in this division"
            )
        
        db_obj = District(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: District, obj_in: DistrictUpdate
    ) -> District:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if code is being updated
        if 'code' in update_data or 'division_id' in update_data:
            existing = db.query(District).filter(
                and_(
                    District.code == update_data.get('code', db_obj.code),
                    District.division_id == update_data.get('division_id', db_obj.division_id),
                    District.id != db_obj.id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="District with this code already exists in this division"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, district_id: int) -> District:
        db_obj = self.get(db, district_id=district_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="District not found"
            )
        
        # Check if district has constituencies
        if db_obj.constituencies:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete district with associated constituencies"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj


class CRUDConstituency:
    def get(self, db: Session, constituency_id: int) -> Optional[Constituency]:
        return db.query(Constituency).filter(Constituency.id == constituency_id).first()
    
    def get_by_number(self, db: Session, number: str) -> Optional[Constituency]:
        return db.query(Constituency).filter(Constituency.number == number).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100,
        district_id: Optional[int] = None, division_id: Optional[int] = None,
        search: Optional[str] = None, is_active: Optional[bool] = None
    ) -> List[Constituency]:
        query = db.query(Constituency)
        
        if district_id:
            query = query.filter(Constituency.district_id == district_id)
        elif division_id:
            # Filter by division through district
            query = query.join(Constituency.district).filter(
                District.division_id == division_id
            )
        
        if search:
            query = query.filter(
                or_(
                    Constituency.name.ilike(f"%{search}%"),
                    Constituency.number.ilike(f"%{search}%")
                )
            )
        
        if is_active is not None:
            query = query.filter(Constituency.is_active == is_active)
        
        return query.order_by(Constituency.number).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: ConstituencyCreate) -> Constituency:
        # Check if constituency with same number exists in same district
        existing = db.query(Constituency).filter(
            and_(
                Constituency.number == obj_in.number,
                Constituency.district_id == obj_in.district_id
            )
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Constituency with this number already exists in this district"
            )
        
        db_obj = Constituency(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def update(
        self, db: Session, *, db_obj: Constituency, obj_in: ConstituencyUpdate
    ) -> Constituency:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Check uniqueness if number is being updated
        if 'number' in update_data or 'district_id' in update_data:
            existing = db.query(Constituency).filter(
                and_(
                    Constituency.number == update_data.get('number', db_obj.number),
                    Constituency.district_id == update_data.get('district_id', db_obj.district_id),
                    Constituency.id != db_obj.id
                )
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Constituency with this number already exists in this district"
                )
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def delete(self, db: Session, *, constituency_id: int) -> Constituency:
        db_obj = self.get(db, constituency_id=constituency_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constituency not found"
            )
        
        # Check if constituency has candidates or results
        if db_obj.candidates or db_obj.election_results:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete constituency with associated candidates or results"
            )
        
        db.delete(db_obj)
        db.commit()
        return db_obj
    
    def get_stats(self, db: Session, constituency_id: int) -> Dict[str, Any]:
        constituency = self.get(db, constituency_id=constituency_id)
        if not constituency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Constituency not found"
            )
        
        # Calculate statistics
        stats = {
            "constituency": constituency,
            "total_candidates": len(constituency.candidates),
            "total_polling_centers": len(constituency.polling_centers),
            "total_voters": constituency.total_voters or 0,
        }
        
        return stats


crud_division = CRUDDivision()
crud_district = CRUDDistrict()
crud_constituency = CRUDConstituency()