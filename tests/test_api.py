from .conftest import login


def test_api_me(client):
    login(client, "employee@test.com")
    response = client.get("/api/v1/me")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["role"] == "employee"
    assert payload["employee"]["employee_code"] == "E003"


def test_employee_directory_api_is_hr_only(client):
    login(client, "employee@test.com")
    assert client.get("/api/v1/employees").status_code == 403
    client.post("/auth/logout")
    login(client, "hr@test.com")
    response = client.get("/api/v1/employees")
    assert response.status_code == 200
    assert len(response.get_json()["data"]) == 3
