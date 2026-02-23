from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    client_id = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    data_profile = Column(String(255), nullable=True)
    status = Column(String(50), default="offline", nullable=False)
    certificate_cn = Column(String(255), nullable=True)
    last_heartbeat = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updates = relationship("ClientUpdate", back_populates="client")
    trust_scores = relationship("TrustScore", back_populates="client")
