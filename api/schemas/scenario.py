from pydantic import BaseModel
from datetime import datetime


class PredictRequest(BaseModel):
    category: str
    store: str
    month: int
    pct_change: float


class PredictResponse(BaseModel):
    baseline_revenue: float
    scenario_revenue: float
    delta: float


class ScenarioRecord(BaseModel):
    id: int
    created_at: datetime
    category: str
    store: str
    month: int
    pct_change: float
    baseline_revenue: float
    scenario_revenue: float
    delta: float

    model_config = {"from_attributes": True}