import os
import tempfile
import pytest
from app.app import create_app

@pytest.fixture
def client():
    # Create isolated temp database per test run
    db_fd, db_path = tempfile.mkstemp()
    app = create_app(db_path=db_path)
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(db_path)

def test_root_endpoint(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.get_json()["service"] == "ACEest Fitness & Gym API"
    assert res.get_json()["status"] == "online"

def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "healthy"

def test_get_programs(client):
    res = client.get("/programs")
    assert res.status_code == 200
    data = res.get_json()
    assert "Fat Loss (FL)" in data
    assert "Muscle Gain (MG)" in data
    assert "Beginner (BG)" in data
    assert data["Fat Loss (FL)"]["factor"] == 22

def test_save_client_and_calorie_calculation(client):
    # 80 kg * factor 35 = 2800 kcal
    payload = {
        "name": "Arjun Sharma",
        "age": 29,
        "weight": 80.0,
        "program": "Muscle Gain (MG)"
    }
    res = client.post("/clients", json=payload)
    assert res.status_code == 201
    assert res.get_json()["client"]["calories"] == 2800

def test_save_client_missing_required_fields(client):
    res = client.post("/clients", json={"name": "NoProgram"})
    assert res.status_code == 400
    assert "required" in res.get_json()["error"]

def test_save_client_invalid_program(client):
    res = client.post("/clients", json={"name": "Test", "program": "NonExistent"})
    assert res.status_code == 400
    assert "Invalid program" in res.get_json()["error"]

def test_get_client_record(client):
    client.post("/clients", json={
        "name": "Priya",
        "age": 25,
        "weight": 55.0,
        "program": "Beginner (BG)"
    })
    res = client.get("/clients/Priya")
    assert res.status_code == 200
    assert res.get_json()["name"] == "Priya"
    assert res.get_json()["calories"] == 1430  # 55 * 26

def test_get_nonexistent_client(client):
    res = client.get("/clients/GhostUser")
    assert res.status_code == 404

def test_log_adherence_progress(client):
    res = client.post("/progress", json={
        "client_name": "Arjun Sharma",
        "week": "Week 41 - 2026",
        "adherence": 90
    })
    assert res.status_code == 201
    assert "Weekly progress logged successfully" in res.get_json()["message"]