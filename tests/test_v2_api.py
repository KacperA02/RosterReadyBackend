import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.database import get_db
from app.v2.main import app


@pytest.fixture()
def client():
    database_url = os.getenv("DATABASE_URL")
    if not database_url or not database_url.startswith("postgresql"):
        pytest.skip("V2 integration tests require a PostgreSQL DATABASE_URL")

    engine = create_engine(database_url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    def override_get_db():
        yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()
    engine.dispose()


def test_register_login_and_create_team(client: TestClient):
    registration = client.post(
        "/api/v2/auth/register",
        json={
            "first_name": "Local",
            "last_name": "Tester",
            "email": "v2-test@example.com",
            "mobile_number": "0000000001",
            "password": "local-test-password",
        },
    )
    assert registration.status_code == 201
    assert registration.json()["memberships"] == []

    login = client.post(
        "/api/v2/auth/login",
        json={"email": "v2-test@example.com", "password": "local-test-password"},
    )
    assert login.status_code == 200
    assert login.json()["access_token"]
    assert login.cookies.get("access_token")

    team = client.post(
        "/api/v2/teams",
        json={
            "name": "Local Test Team",
            "timezone": "Europe/Dublin",
            "contracted_minutes_week": 2250,
            "maximum_minutes_week": 2400,
        },
    )
    assert team.status_code == 201
    assert team.json()["membership"]["role"] == "OWNER"

    teams = client.get("/api/v2/teams")
    assert teams.status_code == 200
    assert [item["name"] for item in teams.json()] == ["Local Test Team"]

    me = client.get("/api/v2/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "v2-test@example.com"


def test_registration_rejects_duplicate_email(client: TestClient):
    payload = {
        "first_name": "Duplicate",
        "last_name": "Tester",
        "email": "duplicate@example.com",
        "password": "local-test-password",
    }
    assert client.post("/api/v2/auth/register", json=payload).status_code == 201
    duplicate = client.post("/api/v2/auth/register", json=payload)
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"] == "Email already registered"
