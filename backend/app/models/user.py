from sqlalchemy import Column, DateTime, String, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
import enum


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    DATA_ENTRY = "data_entry"
    VIEWER = "viewer"


class AdminUser(BaseModel):
    __tablename__ = "admin_user"
    
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.DATA_ENTRY, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Audit logs
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    import_logs = relationship("ImportLog", back_populates="user")
    
    def __repr__(self):
        return f"<AdminUser {self.email}>"