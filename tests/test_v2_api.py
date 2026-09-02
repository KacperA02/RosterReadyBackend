import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.domain.database import get_db
from app.api.v2.app import app


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
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

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


def test_owner_manages_team_skills_and_member_qualifications(client: TestClient):
    register(client, "skills-owner@example.com")
    login(client, "skills-owner@example.com")
    team = create_team(client, "Skills Team")
    team_id = team["id"]

    created = client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "First Aid"})
    assert created.status_code == 201
    skill_id = created.json()["id"]

    duplicate = client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "First Aid"})
    assert duplicate.status_code == 409

    skills = client.get(f"/api/v2/teams/{team_id}/skills")
    assert skills.status_code == 200
    assert skills.json() == [{"id": skill_id, "team_id": team_id, "name": "First Aid"}]

    assigned = client.put(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills/{skill_id}",
        json={"proficiency": "QUALIFIED"},
    )
    assert assigned.status_code == 200
    assert assigned.json()["proficiency"] == "QUALIFIED"

    updated = client.put(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills/{skill_id}",
        json={"proficiency": "ADVANCED"},
    )
    assert updated.status_code == 200
    assert updated.json()["proficiency"] == "ADVANCED"

    qualifications = client.get(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills"
    )
    assert qualifications.status_code == 200
    assert qualifications.json() == [
        {"skill_id": skill_id, "name": "First Aid", "proficiency": "ADVANCED"}
    ]

    removed = client.delete(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills/{skill_id}"
    )
    assert removed.status_code == 204
    assert client.get(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills"
    ).json() == []

    assert client.delete(f"/api/v2/teams/{team_id}/skills/{skill_id}").status_code == 204


def test_employee_can_view_but_cannot_manage_skills(client: TestClient):
    register(client, "permissions-owner@example.com")
    login(client, "permissions-owner@example.com")
    team = create_team(client, "Permissions Team")
    team_id = team["id"]
    skill = client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "Closing"}).json()
    invitation = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "skills-employee@example.com", "role": "EMPLOYEE"},
    ).json()

    register(client, "skills-employee@example.com")
    login(client, "skills-employee@example.com")
    employee = client.post(f"/api/v2/invitations/{invitation['invitation_token']}/accept").json()

    assert client.get(f"/api/v2/teams/{team_id}/skills").status_code == 200
    assert client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "Opening"}).status_code == 403
    assert client.put(
        f"/api/v2/teams/{team_id}/members/{employee['id']}/skills/{skill['id']}",
        json={"proficiency": "QUALIFIED"},
    ).status_code == 403
    assert client.delete(f"/api/v2/teams/{team_id}/skills/{skill['id']}").status_code == 403


def test_qualifications_cannot_cross_team_boundaries(client: TestClient):
    register(client, "boundary-owner@example.com")
    login(client, "boundary-owner@example.com")
    first = create_team(client, "Boundary One")
    second = create_team(client, "Boundary Two")
    skill = client.post(f"/api/v2/teams/{first['id']}/skills", json={"name": "Cash Handling"}).json()

    response = client.put(
        f"/api/v2/teams/{first['id']}/members/{second['membership']['id']}/skills/{skill['id']}",
        json={"proficiency": "QUALIFIED"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Team member not found"


def test_employee_submits_and_manager_reviews_time_request(client: TestClient):
    register(client, "leave-owner@example.com")
    login(client, "leave-owner@example.com")
    team = create_team(client, "Leave Team")
    team_id = team["id"]
    invitation = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "leave-employee@example.com", "role": "EMPLOYEE"},
    ).json()

    register(client, "leave-employee@example.com")
    login(client, "leave-employee@example.com")
    employee = client.post(f"/api/v2/invitations/{invitation['invitation_token']}/accept").json()
    submitted = client.post(
        f"/api/v2/teams/{team_id}/time-requests",
        json={
            "request_type": "HOLIDAY",
            "starts_at": "2026-12-24T00:00:00Z",
            "ends_at": "2026-12-27T00:00:00Z",
            "reason": "Christmas break",
        },
    )
    assert submitted.status_code == 201
    request_id = submitted.json()["id"]
    assert submitted.json()["team_member_id"] == employee["id"]
    assert submitted.json()["status"] == "PENDING"

    assert client.get(f"/api/v2/teams/{team_id}/time-requests/mine").json()[0]["id"] == request_id
    assert client.get(f"/api/v2/teams/{team_id}/time-requests").status_code == 403

    login(client, "leave-owner@example.com")
    pending = client.get(f"/api/v2/teams/{team_id}/time-requests?status=PENDING")
    assert pending.status_code == 200
    assert [item["id"] for item in pending.json()] == [request_id]
    reviewed = client.patch(
        f"/api/v2/teams/{team_id}/time-requests/{request_id}/review",
        json={"status": "APPROVED", "review_note": "Approved for Christmas"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "APPROVED"
    assert reviewed.json()["reviewed_by_member_id"] == team["membership"]["id"]
    assert reviewed.json()["reviewed_at"] is not None

    corrected = client.patch(
        f"/api/v2/teams/{team_id}/time-requests/{request_id}",
        json={
            "request_type": "HOLIDAY",
            "starts_at": "2026-12-23T00:00:00Z",
            "ends_at": "2026-12-27T00:00:00Z",
            "reason": "Manager corrected the start date",
        },
    )
    assert corrected.status_code == 200
    assert corrected.json()["starts_at"].startswith("2026-12-23")

    login(client, "leave-employee@example.com")
    cancelled = client.patch(f"/api/v2/teams/{team_id}/time-requests/{request_id}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELLED"


def test_time_request_period_and_overlap_validation(client: TestClient):
    register(client, "time-validation@example.com")
    login(client, "time-validation@example.com")
    team_id = create_team(client, "Time Validation")["id"]
    endpoint = f"/api/v2/teams/{team_id}/time-requests"

    timezone_missing = client.post(
        endpoint,
        json={
            "request_type": "UNAVAILABLE",
            "starts_at": "2026-11-01T09:00:00",
            "ends_at": "2026-11-01T17:00:00",
        },
    )
    assert timezone_missing.status_code == 422
    assert timezone_missing.json()["detail"] == "Start and end times must include a timezone"

    backwards = client.post(
        endpoint,
        json={
            "request_type": "UNAVAILABLE",
            "starts_at": "2026-11-01T17:00:00Z",
            "ends_at": "2026-11-01T09:00:00Z",
        },
    )
    assert backwards.status_code == 422

    assert client.post(
        endpoint,
        json={
            "request_type": "UNAVAILABLE",
            "starts_at": "2026-11-01T09:00:00Z",
            "ends_at": "2026-11-01T17:00:00Z",
        },
    ).status_code == 201
    overlap = client.post(
        endpoint,
        json={
            "request_type": "PERSONAL_LEAVE",
            "starts_at": "2026-11-01T16:00:00Z",
            "ends_at": "2026-11-01T18:00:00Z",
        },
    )
    assert overlap.status_code == 409


def test_manager_can_submit_time_request_for_employee(client: TestClient):
    register(client, "manual-owner@example.com")
    login(client, "manual-owner@example.com")
    team = create_team(client, "Manual Leave Team")
    team_id = team["id"]
    invitation = client.post(
        f"/api/v2/teams/{team_id}/invitations",
        json={"email": "manual-employee@example.com", "role": "EMPLOYEE"},
    ).json()
    register(client, "manual-employee@example.com")
    login(client, "manual-employee@example.com")
    employee = client.post(f"/api/v2/invitations/{invitation['invitation_token']}/accept").json()

    login(client, "manual-owner@example.com")
    response = client.post(
        f"/api/v2/teams/{team_id}/members/{employee['id']}/time-requests",
        json={
            "request_type": "SICK_LEAVE",
            "starts_at": "2026-10-03T08:00:00+01:00",
            "ends_at": "2026-10-04T08:00:00+01:00",
            "reason": "Recorded by manager",
        },
    )
    assert response.status_code == 201
    assert response.json()["team_member_id"] == employee["id"]


def test_shift_template_rules_skills_and_idempotent_generation(client: TestClient):
    register(client, "shifts-owner@example.com")
    login(client, "shifts-owner@example.com")
    team_id = create_team(client, "Shift Generation Team")["id"]
    skill = client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "Supervisor"}).json()

    template = client.post(
        f"/api/v2/teams/{team_id}/shift-templates",
        json={"name": "Night", "start_time": "22:00:00", "end_time": "06:00:00"},
    )
    assert template.status_code == 201
    template_id = template.json()["id"]
    assert client.post(
        f"/api/v2/teams/{team_id}/shift-templates",
        json={"name": "Night", "start_time": "20:00:00", "end_time": "04:00:00"},
    ).status_code == 409

    requirement = client.put(
        f"/api/v2/teams/{team_id}/shift-templates/{template_id}/skills/{skill['id']}",
        json={"required_count": 1},
    )
    assert requirement.status_code == 200
    rule = client.post(
        f"/api/v2/teams/{team_id}/shift-templates/{template_id}/rules",
        json={
            "weekday": 0,
            "required_staff": 2,
            "effective_from": "2026-09-01",
            "effective_to": None,
        },
    )
    assert rule.status_code == 201

    generated = client.post(
        f"/api/v2/teams/{team_id}/shift-instances/generate",
        json={"period_start": "2026-09-07", "period_end": "2026-09-14"},
    )
    assert generated.status_code == 200
    assert generated.json()["created_count"] == 2
    assert generated.json()["skipped_count"] == 0
    first_instance = generated.json()["instances"][0]
    assert first_instance["required_staff"] == 2
    assert first_instance["starts_at"].startswith("2026-09-07T21:00:00")
    assert first_instance["ends_at"].startswith("2026-09-08T05:00:00")

    repeated = client.post(
        f"/api/v2/teams/{team_id}/shift-instances/generate",
        json={"period_start": "2026-09-07", "period_end": "2026-09-14"},
    )
    assert repeated.status_code == 200
    assert repeated.json()["created_count"] == 0
    assert repeated.json()["skipped_count"] == 2

    instances = client.get(
        f"/api/v2/teams/{team_id}/shift-instances",
        params={"starts_at": "2026-09-01T00:00:00Z", "ends_at": "2026-09-30T00:00:00Z"},
    )
    assert instances.status_code == 200
    assert len(instances.json()) == 2
    instance_skills = client.get(
        f"/api/v2/teams/{team_id}/shift-instances/{first_instance['id']}/skills"
    )
    assert instance_skills.status_code == 200
    assert instance_skills.json() == [
        {"skill_id": skill["id"], "name": "Supervisor", "required_count": 1}
    ]


def test_employee_can_view_but_cannot_configure_shifts(client: TestClient):
    register(client, "shift-permissions-owner@example.com")
    login(client, "shift-permissions-owner@example.com")
    team = create_team(client, "Shift Permissions")
    invitation = client.post(
        f"/api/v2/teams/{team['id']}/invitations",
        json={"email": "shift-viewer@example.com", "role": "EMPLOYEE"},
    ).json()
    register(client, "shift-viewer@example.com")
    login(client, "shift-viewer@example.com")
    client.post(f"/api/v2/invitations/{invitation['invitation_token']}/accept")

    assert client.get(f"/api/v2/teams/{team['id']}/shift-templates").status_code == 200
    forbidden = client.post(
        f"/api/v2/teams/{team['id']}/shift-templates",
        json={"name": "Morning", "start_time": "08:00:00", "end_time": "16:00:00"},
    )
    assert forbidden.status_code == 403
    assert client.post(
        f"/api/v2/teams/{team['id']}/shift-instances/generate",
        json={"period_start": "2026-09-01", "period_end": "2026-09-07"},
    ).status_code == 403


def test_shift_configuration_validation(client: TestClient):
    register(client, "shift-validation-owner@example.com")
    login(client, "shift-validation-owner@example.com")
    team_id = create_team(client, "Shift Validation")["id"]
    invalid = client.post(
        f"/api/v2/teams/{team_id}/shift-templates",
        json={"name": "Zero", "start_time": "09:00:00", "end_time": "09:00:00"},
    )
    assert invalid.status_code == 422

    template = client.post(
        f"/api/v2/teams/{team_id}/shift-templates",
        json={"name": "Day", "start_time": "09:00:00", "end_time": "17:00:00"},
    ).json()
    invalid_period = client.post(
        f"/api/v2/teams/{team_id}/shift-templates/{template['id']}/rules",
        json={
            "weekday": 1,
            "required_staff": 1,
            "effective_from": "2026-10-10",
            "effective_to": "2026-10-01",
        },
    )
    assert invalid_period.status_code == 422
    too_large = client.post(
        f"/api/v2/teams/{team_id}/shift-instances/generate",
        json={"period_start": "2026-01-01", "period_end": "2027-12-31"},
    )
    assert too_large.status_code == 422


def _create_monday_shift(client: TestClient, team_id: int, required_staff: int = 1):
    template = client.post(
        f"/api/v2/teams/{team_id}/shift-templates",
        json={"name": "Monday Day", "start_time": "09:00:00", "end_time": "17:00:00"},
    ).json()
    client.post(
        f"/api/v2/teams/{team_id}/shift-templates/{template['id']}/rules",
        json={
            "weekday": 0,
            "required_staff": required_staff,
            "effective_from": "2026-09-01",
        },
    )
    generated = client.post(
        f"/api/v2/teams/{team_id}/shift-instances/generate",
        json={"period_start": "2026-09-07", "period_end": "2026-09-07"},
    )
    assert generated.status_code == 200
    return template, generated.json()["instances"][0]


def test_cp_sat_creates_and_publishes_feasible_roster(client: TestClient):
    register(client, "solver-owner@example.com")
    login(client, "solver-owner@example.com")
    team = create_team(client, "Solver Team")
    team_id = team["id"]
    _, shift = _create_monday_shift(client, team_id)
    roster = client.post(
        f"/api/v2/teams/{team_id}/rosters",
        json={"period_start": "2026-09-07", "period_end": "2026-09-13"},
    )
    assert roster.status_code == 201
    roster_id = roster.json()["id"]

    solved = client.post(f"/api/v2/teams/{team_id}/rosters/{roster_id}/solve")
    assert solved.status_code == 200
    assert solved.json()["solver_status"] == "OPTIMAL", solved.json()["solver_metadata"]
    assert len(solved.json()["assignments"]) == 1
    assert solved.json()["assignments"][0]["shift_instance_id"] == shift["id"]
    assert solved.json()["assignments"][0]["team_member_id"] == team["membership"]["id"]

    published = client.post(f"/api/v2/teams/{team_id}/rosters/{roster_id}/publish")
    assert published.status_code == 200
    assert published.json()["status"] == "PUBLISHED"
    assert client.post(f"/api/v2/teams/{team_id}/rosters/{roster_id}/solve").status_code == 409


def test_cp_sat_respects_approved_unavailability(client: TestClient):
    register(client, "unavailable-solver@example.com")
    login(client, "unavailable-solver@example.com")
    team = create_team(client, "Unavailable Solver")
    team_id = team["id"]
    _create_monday_shift(client, team_id)
    request = client.post(
        f"/api/v2/teams/{team_id}/time-requests",
        json={
            "request_type": "UNAVAILABLE",
            "starts_at": "2026-09-07T00:00:00Z",
            "ends_at": "2026-09-08T00:00:00Z",
        },
    ).json()
    assert client.patch(
        f"/api/v2/teams/{team_id}/time-requests/{request['id']}/review",
        json={"status": "APPROVED"},
    ).status_code == 200
    roster = client.post(
        f"/api/v2/teams/{team_id}/rosters",
        json={"period_start": "2026-09-07", "period_end": "2026-09-13"},
    ).json()
    solved = client.post(f"/api/v2/teams/{team_id}/rosters/{roster['id']}/solve")
    assert solved.status_code == 200
    assert solved.json()["solver_status"] == "INFEASIBLE"
    assert solved.json()["assignments"] == []
    assert client.post(f"/api/v2/teams/{team_id}/rosters/{roster['id']}/publish").status_code == 409


def test_cp_sat_enforces_required_skills(client: TestClient):
    register(client, "qualified-solver@example.com")
    login(client, "qualified-solver@example.com")
    team = create_team(client, "Qualified Solver")
    team_id = team["id"]
    skill = client.post(f"/api/v2/teams/{team_id}/skills", json={"name": "Keyholder"}).json()
    template, _ = _create_monday_shift(client, team_id)
    assert client.put(
        f"/api/v2/teams/{team_id}/shift-templates/{template['id']}/skills/{skill['id']}",
        json={"required_count": 1},
    ).status_code == 200
    # Regenerate after adding the template requirement in a fresh week.
    generated = client.post(
        f"/api/v2/teams/{team_id}/shift-instances/generate",
        json={"period_start": "2026-09-14", "period_end": "2026-09-14"},
    )
    assert generated.status_code == 200
    roster = client.post(
        f"/api/v2/teams/{team_id}/rosters",
        json={"period_start": "2026-09-14", "period_end": "2026-09-20"},
    ).json()
    assert client.post(
        f"/api/v2/teams/{team_id}/rosters/{roster['id']}/solve"
    ).json()["solver_status"] == "INFEASIBLE"

    assert client.put(
        f"/api/v2/teams/{team_id}/members/{team['membership']['id']}/skills/{skill['id']}",
        json={"proficiency": "QUALIFIED"},
    ).status_code == 200
    solved = client.post(f"/api/v2/teams/{team_id}/rosters/{roster['id']}/solve")
    assert solved.json()["solver_status"] == "OPTIMAL", solved.json()
    assert len(solved.json()["assignments"]) == 1


def test_manual_assignment_is_locked_during_solve_and_can_be_removed(client: TestClient):
    register(client, "manual-roster-owner@example.com")
    login(client, "manual-roster-owner@example.com")
    team = create_team(client, "Manual Roster")
    team_id = team["id"]
    _, shift = _create_monday_shift(client, team_id)
    roster = client.post(
        f"/api/v2/teams/{team_id}/rosters",
        json={"period_start": "2026-09-07", "period_end": "2026-09-13"},
    ).json()
    manual = client.post(
        f"/api/v2/teams/{team_id}/rosters/{roster['id']}/assignments",
        json={
            "shift_instance_id": shift["id"],
            "team_member_id": team["membership"]["id"],
            "reason": "Manager selected this employee",
        },
    )
    assert manual.status_code == 201
    assert manual.json()["source"] == "OVERRIDE"
    assert manual.json()["locked"] is True

    solved = client.post(f"/api/v2/teams/{team_id}/rosters/{roster['id']}/solve")
    assert solved.status_code == 200
    assert solved.json()["solver_status"] == "OPTIMAL"
    assert len(solved.json()["assignments"]) == 1
    assert solved.json()["assignments"][0]["id"] == manual.json()["id"]

    removed = client.delete(
        f"/api/v2/teams/{team_id}/rosters/{roster['id']}/assignments/{manual.json()['id']}",
        params={"reason": "Coverage changed"},
    )
    assert removed.status_code == 204
    detail = client.get(f"/api/v2/teams/{team_id}/rosters/{roster['id']}")
    assert detail.json()["assignments"] == []
    assert detail.json()["solver_status"] == "PENDING"


def test_employee_can_view_but_cannot_manage_rosters(client: TestClient):
    register(client, "roster-permissions-owner@example.com")
    login(client, "roster-permissions-owner@example.com")
    team = create_team(client, "Roster Permissions")
    roster = client.post(
        f"/api/v2/teams/{team['id']}/rosters",
        json={"period_start": "2026-09-07", "period_end": "2026-09-13"},
    ).json()
    invitation = client.post(
        f"/api/v2/teams/{team['id']}/invitations",
        json={"email": "roster-viewer@example.com", "role": "EMPLOYEE"},
    ).json()
    register(client, "roster-viewer@example.com")
    login(client, "roster-viewer@example.com")
    client.post(f"/api/v2/invitations/{invitation['invitation_token']}/accept")

    assert client.get(f"/api/v2/teams/{team['id']}/rosters").status_code == 200
    assert client.get(f"/api/v2/teams/{team['id']}/rosters/{roster['id']}").status_code == 200
    assert client.post(
        f"/api/v2/teams/{team['id']}/rosters",
        json={"period_start": "2026-09-14", "period_end": "2026-09-20"},
    ).status_code == 403
    assert client.post(
        f"/api/v2/teams/{team['id']}/rosters/{roster['id']}/solve"
    ).status_code == 403
