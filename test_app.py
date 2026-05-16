import pytest
from app import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_get_locations(client):
    response = client.get("/locations")
    assert response.status_code == 200
    data = response.get_json()
    assert "locations" in data
    assert len(data["locations"]) == 52

def test_get_single_location(client):
    response = client.get("/locations/13184")
    assert response.status_code == 200
    data = response.get_json()
    assert "coordinates" in data
    assert "lat" in data["coordinates"]
    assert "evses" in data

def test_get_invalid_location(client):
    response = client.get("/locations/invalid")
    assert response.status_code == 404