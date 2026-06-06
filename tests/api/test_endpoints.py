def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_predict_valid(client):
    r = client.post("/api/predict", json={
        "category": "FOODS", "store": "CA_1", "month": 3, "pct_change": 10.0
    })
    assert r.status_code == 200
    data = r.json()
    assert {"baseline_revenue", "scenario_revenue", "delta"} <= data.keys()
    assert data["scenario_revenue"] > data["baseline_revenue"]


def test_predict_invalid_category(client):
    r = client.post("/api/predict", json={
        "category": "INVALID", "store": "CA_1", "month": 3, "pct_change": 0.0
    })
    assert r.status_code == 422


def test_predict_invalid_store(client):
    r = client.post("/api/predict", json={
        "category": "FOODS", "store": "XX_9", "month": 3, "pct_change": 0.0
    })
    assert r.status_code == 422


def test_predict_month_out_of_range(client):
    r = client.post("/api/predict", json={
        "category": "FOODS", "store": "CA_1", "month": 13, "pct_change": 0.0
    })
    assert r.status_code == 422


def test_predict_pct_change_too_low(client):
    r = client.post("/api/predict", json={
        "category": "FOODS", "store": "CA_1", "month": 1, "pct_change": -51.0
    })
    assert r.status_code == 422


def test_history_returns_list(client):
    r = client.get("/api/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_history_contains_submitted_scenario(client):
    client.post("/api/predict", json={
        "category": "HOBBIES", "store": "TX_1", "month": 6, "pct_change": 20.0
    })
    r = client.get("/api/history")
    records = r.json()
    assert len(records) >= 1
    assert records[0]["category"] == "HOBBIES"
    assert records[0]["store"] == "TX_1"


def test_history_max_10_records(client):
    for i in range(12):
        client.post("/api/predict", json={
            "category": "FOODS", "store": "CA_2", "month": 1, "pct_change": float(i)
        })
    r = client.get("/api/history")
    assert len(r.json()) <= 10