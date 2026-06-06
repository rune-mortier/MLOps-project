VALID_PAYLOAD = {
    "category": "FOODS",
    "store": "CA_1",
    "month": 3,
    "pct_change": 10.0,
    "item_id": "FOODS_1_001",
}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_get_items_foods(client):
    r = client.get("/api/items/FOODS")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 17
    assert "FOODS_1_001" in items


def test_get_items_invalid_category(client):
    r = client.get("/api/items/INVALID")
    assert r.status_code == 422


def test_predict_valid(client):
    r = client.post("/api/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert {"baseline_revenue", "scenario_revenue", "delta", "baseline_qty", "scenario_qty"} <= data.keys()
    assert data["scenario_revenue"] > data["baseline_revenue"]


def test_predict_invalid_category(client):
    r = client.post("/api/predict", json={**VALID_PAYLOAD, "category": "INVALID"})
    assert r.status_code == 422


def test_predict_invalid_store(client):
    r = client.post("/api/predict", json={**VALID_PAYLOAD, "store": "XX_9"})
    assert r.status_code == 422


def test_predict_month_out_of_range(client):
    r = client.post("/api/predict", json={**VALID_PAYLOAD, "month": 13})
    assert r.status_code == 422


def test_predict_pct_change_too_low(client):
    r = client.post("/api/predict", json={**VALID_PAYLOAD, "pct_change": -51.0})
    assert r.status_code == 422


def test_predict_invalid_item_for_category(client):
    r = client.post("/api/predict", json={**VALID_PAYLOAD, "item_id": "HOBBIES_1_002"})
    assert r.status_code == 422


def test_history_returns_list(client):
    r = client.get("/api/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_history_contains_submitted_scenario(client):
    client.post("/api/predict", json={**VALID_PAYLOAD, "category": "HOBBIES", "store": "TX_1", "item_id": "HOBBIES_1_002"})
    r = client.get("/api/history")
    records = r.json()
    assert len(records) >= 1
    assert any(rec["category"] == "HOBBIES" for rec in records)


def test_history_max_10_records(client):
    for i in range(12):
        client.post("/api/predict", json={**VALID_PAYLOAD, "pct_change": float(i)})
    r = client.get("/api/history")
    assert len(r.json()) <= 10