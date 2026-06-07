from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from inference import ITEMS_BY_CATEGORY, predict as run_predict
from models.scenario import Scenario
from schemas.scenario import PredictRequest, PredictResponse, ScenarioRecord

router = APIRouter(prefix="/api")

VALID_CATEGORIES = {"FOODS", "HOBBIES", "HOUSEHOLD"}
VALID_STORES     = {"CA_1", "CA_2", "TX_1"}


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/items/{category}")
def get_items(category: str):
    if category not in VALID_CATEGORIES:
        raise HTTPException(422, f"category must be one of {VALID_CATEGORIES}")
    return ITEMS_BY_CATEGORY[category]


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    if req.category not in VALID_CATEGORIES:
        raise HTTPException(422, f"category must be one of {VALID_CATEGORIES}")
    if req.store not in VALID_STORES:
        raise HTTPException(422, f"store must be one of {VALID_STORES}")
    if not 1 <= req.month <= 12:
        raise HTTPException(422, "month must be between 1 and 12")
    if not -50 <= req.pct_change <= 100:
        raise HTTPException(422, "pct_change must be between -50 and 100")
    valid_items = ITEMS_BY_CATEGORY.get(req.category, [])
    if req.item_id not in valid_items:
        raise HTTPException(422, f"item_id not valid for category {req.category}")

    result = run_predict(req.category, req.store, req.month, req.pct_change, req.item_id)

    db.add(Scenario(
        category=req.category,
        store=req.store,
        month=req.month,
        pct_change=req.pct_change,
        item_id=req.item_id,
        baseline_revenue=result["baseline_revenue"],
        scenario_revenue=result["scenario_revenue"],
        delta=result["delta"],
        baseline_qty=result["baseline_qty"],
        scenario_qty=result["scenario_qty"],
    ))
    db.commit()

    return result


@router.get("/history", response_model=List[ScenarioRecord])
def history(db: Session = Depends(get_db)):
    return db.query(Scenario).order_by(Scenario.created_at.desc()).limit(10).all()