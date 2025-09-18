def test_healthcheck(client):
    response = client.get("/api/healthchecker/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Welcome to FastAPI!"
