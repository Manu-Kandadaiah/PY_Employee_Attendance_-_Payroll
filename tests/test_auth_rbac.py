from .conftest import login


def test_login_and_logout(client):
    response = login(client, "employee@test.com")
    assert response.status_code == 200
    assert b"Good day" in response.data
    response = client.post("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_employee_cannot_open_admin(client):
    login(client, "employee@test.com")
    response = client.get("/admin/")
    assert response.status_code == 403


def test_role_dashboards_render(client):
    for email, marker in [
        ("admin@test.com", b"Administration dashboard"),
        ("hr@test.com", b"HR & payroll dashboard"),
        ("manager@test.com", b"Team dashboard"),
        ("employee@test.com", b"Good day"),
    ]:
        client.post("/auth/logout")
        response = login(client, email)
        assert response.status_code == 200
        assert marker in response.data
