import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.database import get_db
from app.v2.main import app


def register(client: TestClient, email: str, mobile_number: str | None = None):
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": email,
        "password": "local-test-password",
    }
    if mobile_number:
        payload["mobile_number"] = mobile_number
    response = client.post("/api/v2/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


def login(client: TestClient, email: str):
    response = client.post(
        "/api/v2/auth/login",
        json={"email": email, "password": "local-test-password"},
    )
    assert response.status_code == 200
    return response.json()


def create_team(client: TestClient, name: str = "Test Team"):
    response = client.post(
        "/api/v2/teams",
        json={
            "name": name,
            "timezone": "Europe/Dublin",
            "contracted_minutes_week": 2250,
            "maximum_minutes_week": 2400,
        },
    )
    assert response.status_code == 201
    return response.json()


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


def test_invitation_acceptance_and_member_management(client: TestClient):
    register(client, "owner@example.com")
    login(client, "owner@example.com")
    team = create_team(client)
    team_id = team["id"]

    invitation = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "employee@example.com", "role": "EMPLOYEE"},
    )
    assert invitation.status_code == 201
    token = invitation.json()["invitation_token"]
    assert token

    duplicate = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "employee@example.com", "role": "EMPLOYEE"},
    )
    assert duplicate.status_code == 409

    register(client, "employee@example.com")
    login(client, "employee@example.com")
    accepted = client.post(f"/api/v2/invitations/{token}/accept")
    assert accepted.status_code == 200
    employee_member_id = accepted.json()["id"]
    assert accepted.json()["role"] == "EMPLOYEE"

    forbidden_invite = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "another@example.com", "role": "EMPLOYEE"},
    )
    assert forbidden_invite.status_code == 403

    login(client, "owner@example.com")
    limits = client.patch(
        f"/api/v2/teams/{team_id}/members/{employee_member_id}/limits",
        json={
            "contracted_minutes_week": 1800,
            "maximum_minutes_week": 2100,
            "maximum_days_week": 4,
            "maximum_consecutive_days": 3,
            "minimum_rest_minutes": 720,
            "effective_from": "2026-09-01",
            "effective_to": None,
        },
    )
    assert limits.status_code == 200
    assert limits.json()["maximum_minutes_week"] == 2100
    assert limits.json()["minimum_rest_minutes"] == 720

    promoted = client.patch(
        f"/api/v2/teams/{team_id}/members/{employee_member_id}/access",
        json={"role": "MANAGER", "status": "ACTIVE"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "MANAGER"

    members = client.get(f"/api/v2/teams/{team_id}/members")
    assert members.status_code == 200
    assert len(members.json()) == 2


def test_invitation_cannot_be_accepted_by_another_email(client: TestClient):
    register(client, "owner-two@example.com")
    login(client, "owner-two@example.com")
    team_id = create_team(client, "Second Team")["id"]
    invitation = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "intended@example.com", "role": "EMPLOYEE"},
    )
    token = invitation.json()["invitation_token"]

    register(client, "wrong-user@example.com")
    login(client, "wrong-user@example.com")
    response = client.post(f"/api/v2/invitations/{token}/accept")
    assert response.status_code == 403
    assert response.json()["detail"] == "Invitation belongs to another user"


def test_member_limits_validation(client: TestClient):
    register(client, "limits-owner@example.com")
    login(client, "limits-owner@example.com")
    team = create_team(client, "Limits Team")
    response = client.patch(
        f"/api/v2/teams/{team['id']}/members/{team['membership']['id']}/limits",
        json={
            "contracted_minutes_week": 2400,
            "maximum_minutes_week": 1200,
            "maximum_days_week": 5,
            "maximum_consecutive_days": 5,
            "minimum_rest_minutes": 660,
            "effective_from": "2026-09-01",
        },
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Maximum weekly minutes cannot be lower than contracted minutes"
