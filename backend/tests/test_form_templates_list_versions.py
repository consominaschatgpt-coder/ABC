from tests.conftest import auth_headers

BASIC_FIELDS = [{"key": "a", "label": "A", "type": "texto"}]


def test_list_versions_returns_all_including_drafts(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    create = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=headers,
    )
    template_id = create.json()["id"]
    client.post(f"/form-templates/{template_id}/versions", json={"fields": BASIC_FIELDS}, headers=headers)

    response = client.get(f"/form-templates/{template_id}/versions", headers=headers)
    assert response.status_code == 200
    versions = response.json()
    assert [v["version_number"] for v in versions] == [1, 2]
