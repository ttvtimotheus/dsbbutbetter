import pytest
from fastapi.testclient import TestClient
import json
import os
import sys

# Füge den Hauptpfad zum Pythonpfad hinzu
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test, ob der Root-Endpunkt erreichbar ist und die richtige Antwort liefert."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "online", "message": "DSB But Better API is running"}

def test_invalid_credentials():
    """Test mit ungültigen Anmeldeinformationen."""
    response = client.post(
        "/api/dsb/parse-plan",
        json={"username": "invalid_user", "password": "invalid_password"}
    )
    assert response.status_code == 401
    
@pytest.mark.skip(reason="Benötigt gültige DSB-Anmeldeinformationen")
def test_valid_credentials():
    """Test mit gültigen Anmeldeinformationen (überspringen, da echte Anmeldeinformationen erforderlich sind)."""
    response = client.post(
        "/api/dsb/parse-plan",
        json={"username": "your_username", "password": "your_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "timetable" in data
    assert "last_updated" in data
    assert "status" in data
    assert data["status"] == "success"
