from datetime import datetime
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    roles = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    evaluations = relationship("Evaluation", back_populates="owner", cascade="all, delete-orphan")

    @property
    def role_list(self) -> list[str]:
        if not self.roles:
            return []
        return [role.strip() for role in self.roles.split(",") if role.strip()]

