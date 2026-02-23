from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base


class TrustScore(Base):
    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    deviation_avg = Column(Float, nullable=True)
    is_flagged = Column(Boolean, default=False, nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    client = relationship("Client", back_populates="trust_scores")
    round = relationship("TrainingRound", back_populates="trust_scores")
