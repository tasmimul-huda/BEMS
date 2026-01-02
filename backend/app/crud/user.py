from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from app.models.user import AdminUser
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException, status


class CRUDUser:
    def get(self, db: Session, user_id: int) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.id == user_id).first()
    
    def get_by_email(self, db: Session, email: str) -> Optional[AdminUser]:
        return db.query(AdminUser).filter(AdminUser.email == email).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[AdminUser]:
        return db.query(AdminUser).offset(skip).limit(limit).all()
    
    def create(self, db: Session, *, obj_in: UserCreate) -> AdminUser:
        # Check if user already exists
        db_user = self.get_by_email(db, email=obj_in.email)
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(obj_in.password)
        db_user = AdminUser(
            email=obj_in.email,
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
            role=obj_in.role,
            is_active=obj_in.is_active,
            is_verified=obj_in.is_verified
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def update(
        self, db: Session, *, db_user: AdminUser, obj_in: UserUpdate
    ) -> AdminUser:
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # Handle password update separately if provided
        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        
        for field in update_data:
            setattr(db_user, field, update_data[field])
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    
    def authenticate(
        self, db: Session, *, email: str, password: str
    ) -> Optional[AdminUser]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def delete(self, db: Session, *, user_id: int) -> AdminUser:
        user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        db.delete(user)
        db.commit()
        return user
    
    def update_last_login(self, db: Session, user: AdminUser):
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)


crud_user = CRUDUser()