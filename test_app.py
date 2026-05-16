import pytest
from app import app, create_tables, import_integrated_data

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_get_locations(client):
    response = client.get("/locations")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 52

def test_get_single_location(client):
    response = client.get("/locations/13184")
    assert response.status_code == 200
    data = response.get_json()
    assert data["location_reference"] == "13184"
    assert "evses" in data

def test_get_invalid_location(client):
    response = client.get("/locations/invalid")
    assert response.status_code == 404