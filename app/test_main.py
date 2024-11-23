"""
Test for the app
"""

import requests

BASE_URL = "http://app:5000"

def test_ready_endpoint():
    """Test the readiness endpoint."""
    response = requests.get(f"{BASE_URL}/ready", timeout=5)
    assert response.status_code in [200, 503], "Unexpected status code for /ready"
    if response.status_code == 200:
        assert response.text == "Application is ready"
    else:
        assert response.text == "Application is not ready"

def test_odd_endpoint():
    """Test the odd number generation endpoint."""
    response = requests.get(f"{BASE_URL}/odd", timeout=5)
    assert response.status_code == 200, "Unexpected status code for /odd"
    data = response.json()
    assert isinstance(data["Odd number"], int), "'Odd number' is not an integer"
    assert data["Odd number"] % 2 != 0, "'Odd number' is not odd"
