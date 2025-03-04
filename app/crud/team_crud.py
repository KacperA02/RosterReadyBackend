from sqlalchemy.orm import Session, joinedload
from app.models.team_model import Team
from app.models.user_model import User
from app.models.shift_model import Shift
from app.models.day_model import Day
from app.models.role_model import Role
from app.schemas.team_schema import TeamCreate
from app.schemas.user_schema import UserResponse
# from app.association import team_user, day_shift_team


def create_team(db: Session, team: TeamCreate, current_user: UserResponse):
    # Fetch the creator (current authenticated user)
    creator = db.query(User).filter(User.id == current_user.id).first()
    if not creator:
        return None, "Creator not found"

    # Add the "employer" role to the creator (if not already added)
    employer_role = db.query(Role).filter(Role.name == "Employer").first()
    if employer_role and employer_role not in creator.roles:
        creator.roles.append(employer_role)
        db.commit()
    # checking if the user is already part of a team
    if creator.team_id is not None:
        return None, "You are part of a team, leave the current team to create one"
    # Create the team
    new_team = Team(name=team.name, creator_id=creator.id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    creator.team_id = new_team.id
    db.commit()  
    return new_team, None



# getting a single team
def get_team(db: Session, team_id: int):
    team = db.query(Team).options(joinedload(Team.users)).filter(Team.id == team_id).first()
    if not team:
        return None
    return team

# updating the users
def update_team_users(db: Session, team_id: int, new_user_ids: list[int]):
    # Fetch the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return None, "Team not found"

    # validation
    new_users = db.query(User).filter(User.id.in_(new_user_ids)).all()
    if len(new_users) != len(new_user_ids):
        return None, "One of the user IDs are invalid"

    # Add new members
    team.users.extend(new_users)
    db.commit()

    return team, None

# def get_users_for_team(db: Session, team_id: int):
#     return db.query(User).join(team_user).filter(team_user.c.team_id == team_id).all()

# def get_shifts_for_team(db: Session, team_id: int):
#     return db.query(Shift).join(day_shift_team).filter(day_shift_team.c.team_id == team_id).all()

# def get_days_for_team(db: Session, team_id: int):
#     return db.query(Day).join(day_shift_team).filter(day_shift_team.c.team_id == team_id).all()