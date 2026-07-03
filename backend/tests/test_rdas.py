from tests.conftest import auth_headers


def _create_draft(client, headers, contract, team, form_version, answers=None):
    payload = {
        "contract_id": str(contract.id),
        "team_id": str(team.id),
        "form_template_version_id": str(form_version.id),
        "answers": answers or {"houve_atividade": "sim"},
    }
    return client.post("/rdas", json=payload, headers=headers)


def test_coletor_creates_and_submits_rda(
    client, coletor_in_team, team, contract, published_form_version
):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")

    create = _create_draft(
        client,
        headers,
        contract,
        team,
        published_form_version,
        answers={"houve_atividade": "sim", "tipo_supressao": "Fauna"},
    )
    assert create.status_code == 201
    rda = create.json()
    assert rda["status"] == "rascunho"
    assert rda["original_answers"] is None

    submit = client.post(f"/rdas/{rda['id']}/submit", headers=headers)
    assert submit.status_code == 200
    submitted = submit.json()
    assert submitted["status"] == "enviado"
    assert submitted["original_answers"] == {"houve_atividade": "sim", "tipo_supressao": "Fauna"}
    assert submitted["submitted_at"] is not None


def test_submit_fails_when_required_field_missing(
    client, coletor_in_team, team, contract, published_form_version
):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    create = _create_draft(
        client, headers, contract, team, published_form_version, answers={"houve_atividade": "sim"}
    )
    rda_id = create.json()["id"]

    submit = client.post(f"/rdas/{rda_id}/submit", headers=headers)
    assert submit.status_code == 422
    assert any("tipo_supressao" in msg for msg in submit.json()["detail"])


def test_conditional_field_not_required_when_condition_false(
    client, coletor_in_team, team, contract, published_form_version
):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    create = _create_draft(
        client, headers, contract, team, published_form_version, answers={"houve_atividade": "nao"}
    )
    rda_id = create.json()["id"]

    submit = client.post(f"/rdas/{rda_id}/submit", headers=headers)
    assert submit.status_code == 200


def test_unknown_field_rejected(client, coletor_in_team, team, contract, published_form_version):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = _create_draft(
        client, headers, contract, team, published_form_version, answers={"campo_fantasma": "x"}
    )
    assert response.status_code == 422


def test_coletor_outside_team_cannot_create(
    client, coletor_user, team, contract, published_form_version
):
    headers = auth_headers(client, "coletor@consominas.com", "senha123")
    response = _create_draft(client, headers, contract, team, published_form_version)
    assert response.status_code == 403


def test_full_approval_flow_with_audit_trail(
    client, coletor_in_team, coordenador_in_team, team, contract, published_form_version
):
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    coordenador_headers = auth_headers(client, "coordenador@consominas.com", "senha123")

    create = _create_draft(
        client,
        coletor_headers,
        contract,
        team,
        published_form_version,
        answers={"houve_atividade": "sim", "tipo_supressao": "Fauna"},
    )
    rda_id = create.json()["id"]
    client.post(f"/rdas/{rda_id}/submit", headers=coletor_headers)

    review = client.post(f"/rdas/{rda_id}/start-review", headers=coordenador_headers)
    assert review.status_code == 200
    assert review.json()["status"] == "em_revisao"

    fix = client.patch(
        f"/rdas/{rda_id}/answers",
        json={"answers": {"tipo_supressao": "Flora"}, "comment": "corrigido apos conferencia em campo"},
        headers=coordenador_headers,
    )
    assert fix.status_code == 200
    assert fix.json()["answers"]["tipo_supressao"] == "Flora"
    # dado original preservado mesmo apos edicao do coordenador
    assert fix.json()["original_answers"]["tipo_supressao"] == "Fauna"

    approve = client.post(
        f"/rdas/{rda_id}/approve", json={"comment": "ok"}, headers=coordenador_headers
    )
    assert approve.status_code == 200
    assert approve.json()["status"] == "aprovado"

    audit = client.get(f"/rdas/{rda_id}/audit-log", headers=coordenador_headers)
    assert audit.status_code == 200
    actions = [entry["action"] for entry in audit.json()]
    assert actions == ["criado", "enviado", "iniciada_revisao", "editado", "aprovado"]

    edit_entry = next(e for e in audit.json() if e["action"] == "editado")
    assert edit_entry["field_changes"] == [
        {"field": "tipo_supressao", "old_value": "Fauna", "new_value": "Flora"}
    ]
    assert edit_entry["comment"] == "corrigido apos conferencia em campo"


def test_reject_returns_to_coletor_for_correction_and_resubmit(
    client, coletor_in_team, coordenador_in_team, team, contract, published_form_version
):
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    coordenador_headers = auth_headers(client, "coordenador@consominas.com", "senha123")

    create = _create_draft(
        client,
        coletor_headers,
        contract,
        team,
        published_form_version,
        answers={"houve_atividade": "sim", "tipo_supressao": "Fauna"},
    )
    rda_id = create.json()["id"]
    client.post(f"/rdas/{rda_id}/submit", headers=coletor_headers)

    reject = client.post(
        f"/rdas/{rda_id}/reject", json={"reason": "foto ilegivel"}, headers=coordenador_headers
    )
    assert reject.status_code == 200
    assert reject.json()["status"] == "reprovado"
    assert reject.json()["review_comment"] == "foto ilegivel"

    fix = client.patch(
        f"/rdas/{rda_id}/answers",
        json={"answers": {"observacoes": "corrigido"}},
        headers=coletor_headers,
    )
    assert fix.status_code == 200

    resubmit = client.post(f"/rdas/{rda_id}/submit", headers=coletor_headers)
    assert resubmit.status_code == 200
    assert resubmit.json()["status"] == "enviado"
    # original_answers continua sendo o da primeira submissao
    assert "observacoes" not in resubmit.json()["original_answers"]


def test_coordenador_outside_team_cannot_review(
    client, coletor_in_team, coordenador_user, team, contract, published_form_version
):
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    coordenador_headers = auth_headers(client, "coordenador@consominas.com", "senha123")

    create = _create_draft(
        client, coletor_headers, contract, team, published_form_version, answers={"houve_atividade": "nao"}
    )
    rda_id = create.json()["id"]
    client.post(f"/rdas/{rda_id}/submit", headers=coletor_headers)

    response = client.post(f"/rdas/{rda_id}/start-review", headers=coordenador_headers)
    assert response.status_code == 403


def test_coletor_cannot_see_others_rda(
    client, coletor_in_team, team, contract, published_form_version, db_session, organization
):
    from tests.conftest import make_user, assign_to_team
    from app.models.user import Role

    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    create = _create_draft(
        client, coletor_headers, contract, team, published_form_version, answers={"houve_atividade": "nao"}
    )
    rda_id = create.json()["id"]

    other = make_user(
        db_session, organization, email="outro@consominas.com", password="senha123", role=Role.COLETOR
    )
    assign_to_team(db_session, other, team)
    other_headers = auth_headers(client, "outro@consominas.com", "senha123")

    response = client.get(f"/rdas/{rda_id}", headers=other_headers)
    assert response.status_code == 403


def test_list_rdas_scoped_by_role(
    client, coletor_in_team, coordenador_in_team, team, contract, published_form_version
):
    coletor_headers = auth_headers(client, "coletor@consominas.com", "senha123")
    coordenador_headers = auth_headers(client, "coordenador@consominas.com", "senha123")

    _create_draft(client, coletor_headers, contract, team, published_form_version, answers={"houve_atividade": "nao"})
    _create_draft(client, coletor_headers, contract, team, published_form_version, answers={"houve_atividade": "sim", "tipo_supressao": "Fauna"})

    coletor_list = client.get("/rdas", headers=coletor_headers).json()
    assert len(coletor_list) == 2

    coordenador_list = client.get("/rdas", headers=coordenador_headers).json()
    assert len(coordenador_list) == 2
