from tests.conftest import auth_headers

BASIC_FIELDS = [
    {"key": "houve_atividade", "label": "Houve atividade?", "type": "selecao_unica", "options": ["sim", "nao"]},
    {
        "key": "tipo_supressao",
        "label": "Tipo de supressao",
        "type": "selecao_unica",
        "options": ["Fauna", "Flora", "Biota aquatica"],
        "condition": {"field": "houve_atividade", "equals": "sim"},
    },
    {"key": "foto_local", "label": "Foto do local", "type": "foto"},
]


def test_admin_creates_template_with_draft_version(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=headers,
    )
    assert response.status_code == 201
    template_id = response.json()["id"]

    detail = client.get(f"/form-templates/{template_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["current_version"] is None  # ainda nao publicado


def test_unknown_version_returns_404(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    create = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=headers,
    )
    template_id = create.json()["id"]

    response = client.get(
        f"/form-templates/{template_id}/versions/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert response.status_code == 404


def test_full_versioning_flow(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    create = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=headers,
    )
    template_id = create.json()["id"]

    new_version = client.post(
        f"/form-templates/{template_id}/versions",
        json={"fields": BASIC_FIELDS},
        headers=headers,
    )
    assert new_version.status_code == 201
    assert new_version.json()["version_number"] == 2
    version_id = new_version.json()["id"]

    publish = client.post(
        f"/form-templates/{template_id}/versions/{version_id}/publish", headers=headers
    )
    assert publish.status_code == 200
    assert publish.json()["is_published"] is True

    detail = client.get(f"/form-templates/{template_id}", headers=headers)
    assert detail.json()["current_version"]["id"] == version_id

    second_version = client.post(
        f"/form-templates/{template_id}/versions",
        json={"fields": BASIC_FIELDS},
        headers=headers,
    )
    second_version_id = second_version.json()["id"]
    client.post(
        f"/form-templates/{template_id}/versions/{second_version_id}/publish", headers=headers
    )

    first_version_detail = client.get(
        f"/form-templates/{template_id}/versions/{version_id}", headers=headers
    )
    assert first_version_detail.json()["is_published"] is False

    detail_after = client.get(f"/form-templates/{template_id}", headers=headers)
    assert detail_after.json()["current_version"]["id"] == second_version_id


def test_duplicate_field_keys_rejected(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    fields = [
        {"key": "a", "label": "A", "type": "texto"},
        {"key": "a", "label": "A duplicado", "type": "texto"},
    ]
    response = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": fields},
        headers=headers,
    )
    assert response.status_code == 422


def test_selection_field_requires_options(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    fields = [{"key": "a", "label": "A", "type": "selecao_unica"}]
    response = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": fields},
        headers=headers,
    )
    assert response.status_code == 422


def test_coletor_can_read_but_not_create(client, admin_user, coletor_user, contract):
    admin_headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    create = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=admin_headers,
    )
    template_id = create.json()["id"]

    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    read_response = client.get(f"/form-templates/{template_id}", headers=coletor_headers)
    assert read_response.status_code == 200

    create_response = client.post(
        "/form-templates",
        json={"name": "Outro", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=coletor_headers,
    )
    assert create_response.status_code == 403


def test_get_version_by_id_without_template_context(client, admin_user, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    create = client.post(
        "/form-templates",
        json={"name": "RDA MRN", "contract_id": str(contract.id), "fields": BASIC_FIELDS},
        headers=headers,
    )
    template_id = create.json()["id"]
    versions = client.get(f"/form-templates/{template_id}/versions", headers=headers).json()
    version_id = versions[0]["id"]

    response = client.get(f"/form-template-versions/{version_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["id"] == version_id
