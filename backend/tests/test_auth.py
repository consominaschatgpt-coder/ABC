from tests.conftest import auth_headers


def test_login_success(client, admin_user):
    response = client.post(
        "/auth/login",
        json={"email": "admin@consominas.com", "password": "senha-forte-123"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password(client, admin_user):
    response = client.post(
        "/auth/login",
        json={"email": "admin@consominas.com", "password": "senha-errada"},
    )
    assert response.status_code == 401


def test_me_requires_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401


def test_me_returns_current_user(client, admin_user):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "admin@consominas.com"
