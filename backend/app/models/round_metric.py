from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class RoundMetric(Base):
    __tablename__ = "round_metrics"

    id = Column(Integer, primary_key=True, index=True)
    round_id = Column(Integer, ForeignKey("training_rounds.id"), nullable=False, index=True)
    aggregation_method = Column(String(100), nullable=True)
    weiszfeld_iterations = Column(Integer, nullable=True)
    convergence_epsilon = Column(Float, nullable=True)
    encryption_overhead_ms = Column(Integer, nullable=True)
    aggregation_time_ms = Column(Integer, nullable=True)
    poisoned_clients_detected = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    round = relationship("TrainingRound", back_populates="metrics")
