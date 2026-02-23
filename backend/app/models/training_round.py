from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class TrainingRound(Base):
    __tablename__ = "training_rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False, index=True)
    job_id = Column(String(255), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    num_clients = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    global_loss = Column(Float, nullable=True)
    global_auc = Column(Float, nullable=True)

    updates = relationship("ClientUpdate", back_populates="round")
    metrics = relationship("RoundMetric", back_populates="round")
    trust_scores = relationship("TrustScore", back_populates="round")
