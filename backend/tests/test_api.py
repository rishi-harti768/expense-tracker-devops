import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def create(client, **overrides):
    body = {"title": "Lunch", "amount": 12.5, "category": "FOOD"} | overrides
    return client.post("/api/expenses", json=body)

def test_health(client):
    assert client.get("/health").json() == {"status": "UP"}

def test_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "ExpenseTracker API"

def test_create_expense(client):
    response = create(client, title="Bus pass", amount=30, category="TRANSPORT")
    assert response.status_code == 201
    assert response.json()["title"] == "Bus pass"

def test_create_expense_rejects_zero_amount(client):
    response = create(client, amount=0)
    assert response.status_code == 422

def test_get_missing_expense(client):
    assert client.get("/api/expenses/999999999").status_code == 404

def test_update_and_delete_expense(client):
    expense_id = create(client, title="Milk").json()["id"]
    response = client.put(f"/api/expenses/{expense_id}", json={"category": "BILLS"})
    assert response.json()["category"] == "BILLS"
    assert client.delete(f"/api/expenses/{expense_id}").status_code == 204
    assert client.get(f"/api/expenses/{expense_id}").status_code == 404

def test_stats_totals(client):
    before = client.get("/api/expenses/stats").json()
    create(client, amount=10.25, category="FOOD")
    create(client, amount=4.75, category="FOOD")
    after = client.get("/api/expenses/stats").json()
    assert after["food"] - before["food"] == pytest.approx(15.0)
    assert after["totalAmount"] - before["totalAmount"] == pytest.approx(15.0)
