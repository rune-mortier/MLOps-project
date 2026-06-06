from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    category = Column(String(20))
    store = Column(String(10))
    month = Column(Integer)
    pct_change = Column(Float)
    baseline_revenue = Column(Float)
    scenario_revenue = Column(Float)
    delta = Column(Float)