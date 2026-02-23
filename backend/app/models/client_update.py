from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class ClientUpdate(Base):
    __tablename__ = "client_updates"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    local_loss = Column(Float, nullable=True)
    local_auc = Column(Float, nullable=True)
    num_samples = Column(Integer, nullable=True)
    euclidean_distance = Column(Float, nullable=True)
    encryption_status = Column(String(50), nullable=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    round = relationship("TrainingRound", back_populates="updates")
    client = relationship("Client", back_populates="updates")
