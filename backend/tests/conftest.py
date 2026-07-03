import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://rda:rda@localhost:5432/rda_campo_test"
)
os.environ.setdefault("SECRET_KEY", "test-secret-key")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.contract import Contract
from app.models.organization import Organization
from app.models.team import Team
from app.models.user import Role, User

engine = create_engine(settings.database_url)
TestSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def organization(db_session):
    org = Organization(name="Consominas")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture
def contract(db_session, organization):
    contract = Contract(name="MRN", organization_id=organization.id)
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def team(db_session, contract):
    team = Team(name="Frente 1", contract_id=contract.id)
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


def make_user(db_session, organization, *, email, password, role):
    user = User(
        organization_id=organization.id,
        name=email.split("@")[0],
        email=email,
        hashed_password=hash_password(password),
        role=role,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, organization):
    return make_user(
        db_session,
        organization,
        email="admin@consominas.com",
        password="senha-forte-123",
        role=Role.ADMIN,
    )


@pytest.fixture
def coletor_user(db_session, organization):
    return make_user(
        db_session,
        organization,
        email="coletor@consominas.com",
        password="senha123",
        role=Role.COLETOR,
    )


def auth_headers(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
