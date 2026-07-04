from tests.conftest import auth_headers


def test_coletor_sees_own_teams(client, coletor_in_team, team):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.get("/users/me/teams", headers=headers)
    assert response.status_code == 200
    assert [t["id"] for t in response.json()] == [str(team.id)]


def test_coletor_can_list_form_templates(client, coletor_user, published_form_version):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.get("/form-templates", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
