from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable

from app.domain.models import Base


EXPECTED_TABLES = {
    "assignment_events",
    "assignments",
    "member_skills",
    "rosters",
    "shift_instance_skills",
    "shift_instances",
    "shift_template_rules",
    "shift_template_skills",
    "shift_templates",
    "skills",
    "team_invitations",
    "team_members",
    "team_policies",
    "teams",
    "time_requests",
    "users",
}


def test_normalized_schema_contains_expected_tables():
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_assignments_do_not_duplicate_team_or_date_data():
    assignment_columns = set(Base.metadata.tables["assignments"].columns.keys())

    assert "team_id" not in assignment_columns
    assert "day_id" not in assignment_columns
    assert "week_id" not in assignment_columns
    assert {
        "roster_id",
        "shift_instance_id",
        "team_member_id",
    }.issubset(assignment_columns)


def test_users_are_not_tied_to_one_team():
    assert "team_id" not in Base.metadata.tables["users"].columns
    assert "team_members" in Base.metadata.tables


def test_every_table_compiles_for_postgresql():
    dialect = postgresql.dialect()

    for table in Base.metadata.sorted_tables:
        ddl = str(CreateTable(table).compile(dialect=dialect))
        assert f"CREATE TABLE {table.name}" in ddl

