from pydantic import BaseModel
from datetime import datetime


class PredictRequest(BaseModel):
    category: str
    store: str
    month: int
    pct_change: float
    item_id: str


class PredictResponse(BaseModel):
    baseline_revenue: float
    scenario_revenue: float
    delta: float
    baseline_qty: float
    scenario_qty: float


class ScenarioRecord(BaseModel):
    id: int
    created_at: datetime
    category: str
    store: str
    month: int
    pct_change: float
    item_id: str
    baseline_revenue: float
    scenario_revenue: float
    delta: float
    baseline_qty: float
    scenario_qty: float

    model_config = {"from_attributes": True}