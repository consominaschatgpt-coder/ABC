import openpyxl
import pytest

from app.models.form_template import FormTemplate, FormTemplateVersion
from tests.conftest import auth_headers


@pytest.fixture
def form_version_with_gps(db_session, contract):
    template = FormTemplate(name="RDA com GPS", contract_id=contract.id)
    db_session.add(template)
    db_session.flush()

    version = FormTemplateVersion(
        template_id=template.id,
        version_number=1,
        is_published=True,
        schema=[
            {"key": "observacoes", "label": "Observacoes", "type": "texto", "required": True},
            {"key": "gps", "label": "Localizacao", "type": "localizacao", "required": False},
        ],
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)
    return version


@pytest.fixture
def approved_rda(client, coletor_in_team, coordenador_in_team, team, contract, form_version_with_gps):
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    coordenador_headers = auth_headers(client, "coordenador@consominas.com", "senha123")

    create = client.post(
        "/rdas",
        json={
            "contract_id": str(contract.id),
            "team_id": str(team.id),
            "form_template_version_id": str(form_version_with_gps.id),
            "answers": {"observacoes": "tudo certo", "gps": "-19.9,-43.9"},
        },
        headers=coletor_headers,
    )
    rda_id = create.json()["id"]
    client.post(f"/rdas/{rda_id}/submit", headers=coletor_headers)
    client.post(f"/rdas/{rda_id}/approve", json={"comment": "ok"}, headers=coordenador_headers)
    return rda_id


def test_pdf_report_requires_approved_rda(client, coletor_in_team, team, contract, published_form_version):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    create = client.post(
        "/rdas",
        json={
            "contract_id": str(contract.id),
            "team_id": str(team.id),
            "form_template_version_id": str(published_form_version.id),
            "answers": {"houve_atividade": "nao"},
        },
        headers=headers,
    )
    rda_id = create.json()["id"]

    response = client.get(f"/reports/rdas/{rda_id}/pdf", headers=headers)
    assert response.status_code == 409


def test_pdf_report_for_approved_rda(client, admin_user, approved_rda):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(f"/reports/rdas/{approved_rda}/pdf", headers=headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_excel_report_for_approved_rda(client, admin_user, approved_rda):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(f"/reports/rdas/{approved_rda}/excel", headers=headers)
    assert response.status_code == 200

    import io

    wb = openpyxl.load_workbook(io.BytesIO(response.content))
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0] == ("Equipe", "Coletor", "Status", "Enviado em", "Revisado em", "Campo", "Resposta")
    assert any(row[5] == "Observacoes" and row[6] == "tudo certo" for row in rows[1:])


def test_coletor_cannot_view_others_report(client, admin_user, approved_rda, db_session, organization):
    from app.models.user import Role

    from tests.conftest import make_user

    other = make_user(
        db_session, organization, email="outro@consominas.com", password="senha123", role=Role.COLETOR
    )
    headers = auth_headers(client, "outro@consominas.com", "senha123")
    response = client.get(f"/reports/rdas/{approved_rda}/pdf", headers=headers)
    assert response.status_code == 403


def test_consolidated_pdf_report(client, admin_user, approved_rda, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(
        "/reports/consolidated", params={"contract_id": str(contract.id), "format": "pdf"}, headers=headers
    )
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_consolidated_csv_report(client, admin_user, approved_rda, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(
        "/reports/consolidated", params={"contract_id": str(contract.id), "format": "csv"}, headers=headers
    )
    assert response.status_code == 200
    text = response.content.decode("utf-8")
    assert "equipe,coletor,status" in text
    assert "tudo certo" in text


def test_consolidated_geojson_report_includes_gps_point(client, admin_user, approved_rda, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(
        "/reports/consolidated",
        params={"contract_id": str(contract.id), "format": "geojson"},
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 1
    assert data["features"][0]["geometry"]["coordinates"] == [-43.9, -19.9]


def test_consolidated_kmz_report(client, admin_user, approved_rda, contract):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    response = client.get(
        "/reports/consolidated", params={"contract_id": str(contract.id), "format": "kmz"}, headers=headers
    )
    assert response.status_code == 200
    assert response.content[:2] == b"PK"  # KMZ e um zip


def test_consolidated_report_excludes_non_approved(client, admin_user, coletor_in_team, team, contract, published_form_version):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    client.post(
        "/rdas",
        json={
            "contract_id": str(contract.id),
            "team_id": str(team.id),
            "form_template_version_id": str(published_form_version.id),
            "answers": {"houve_atividade": "nao"},
        },
        headers=coletor_headers,
    )

    response = client.get(
        "/reports/consolidated", params={"contract_id": str(contract.id), "format": "geojson"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["features"] == []


def test_admin_sets_custom_report_template(client, admin_user, contract, approved_rda):
    headers = auth_headers(client, "admin@consominas.com", "senha-forte-123")

    get_before = client.get(f"/reports/templates/{contract.id}", headers=headers)
    assert get_before.status_code == 200
    assert get_before.json() is None

    custom_html = "<html><body><h1>Modelo customizado {{ contract_name }}</h1></body></html>"
    upsert = client.put(
        f"/reports/templates/{contract.id}",
        json={"name": "Modelo MRN", "html_template": custom_html},
        headers=headers,
    )
    assert upsert.status_code == 200
    assert upsert.json()["html_template"] == custom_html

    get_after = client.get(f"/reports/templates/{contract.id}", headers=headers)
    assert get_after.json()["name"] == "Modelo MRN"

    pdf_response = client.get(f"/reports/rdas/{approved_rda}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


def test_coletor_cannot_set_report_template(client, coletor_user, contract):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = client.put(
        f"/reports/templates/{contract.id}",
        json={"name": "x", "html_template": "<p>x</p>"},
        headers=headers,
    )
    assert response.status_code == 403
