from tests.conftest import auth_headers


def test_admin_adds_and_removes_team_member(client, admin_user, coletor_user, team):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")

    add = client.post(
        f"/teams/{team.id}/members", json={"user_id": str(coletor_user.id)}, headers=headers
    )
    assert add.status_code == 201

    members = client.get(f"/teams/{team.id}/members", headers=headers)
    assert members.status_code == 200
    assert [m["id"] for m in members.json()] == [str(coletor_user.id)]

    duplicate = client.post(
        f"/teams/{team.id}/members", json={"user_id": str(coletor_user.id)}, headers=headers
    )
    assert duplicate.status_code == 409

    remove = client.delete(f"/teams/{team.id}/members/{coletor_user.id}", headers=headers)
    assert remove.status_code == 204

    members_after = client.get(f"/teams/{team.id}/members", headers=headers)
    assert members_after.json() == []


def test_coletor_cannot_add_team_member(client, coletor_user, team):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.post(
        f"/teams/{team.id}/members", json={"user_id": str(coletor_user.id)}, headers=headers
    )
    assert response.status_code == 403
