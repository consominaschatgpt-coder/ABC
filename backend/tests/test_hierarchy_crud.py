from tests.conftest import auth_headers


def test_admin_creates_contract_and_team(client, admin_user, organization):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")

    contract_resp = client.post(
        "/contracts",
        json={"name": "MRN", "organization_id": str(organization.id)},
        headers=headers,
    )
    assert contract_resp.status_code == 201
    contract_id = contract_resp.json()["id"]

    team_resp = client.post(
        "/teams",
        json={"name": "Frente 1", "contract_id": contract_id},
        headers=headers,
    )
    assert team_resp.status_code == 201
    assert team_resp.json()["contract_id"] == contract_id


def test_admin_creates_user(client, admin_user, organization):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")

    response = client.post(
        "/users",
        json={
            "name": "Joao Coletor",
            "email": "joao@consominas.com",
            "password": "senha123",
            "role": "coletor",
            "organization_id": str(organization.id),
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["role"] == "coletor"


def test_coletor_cannot_list_users(client, admin_user, coletor_user):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.get("/users", headers=headers)
    assert response.status_code == 403


def test_coletor_cannot_create_contract(client, coletor_user, organization):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.post(
        "/contracts",
        json={"name": "MRN", "organization_id": str(organization.id)},
        headers=headers,
    )
    assert response.status_code == 403


def test_duplicate_email_rejected(client, admin_user, organization):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    payload = {
        "name": "Duplicado",
        "email": "admin@consominas.com",
        "password": "outrasenha",
        "role": "coletor",
        "organization_id": str(organization.id),
    }
    response = client.post("/users", json=payload, headers=headers)
    assert response.status_code == 409
