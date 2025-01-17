from sqlalchemy.orm import Session
from app.models.team_model import Team, team_members
from app.models.user_model import User
from app.schemas.team_schema import TeamCreate

def create_team(db: Session, team: TeamCreate):
    # Fetch the creator
    creator = db.query(User).filter(User.id == team.creator_id).first()
    if not creator:
        return None, "Creator not found"

    # Create the team
    new_team = Team(name=team.name, creator_id=team.creator_id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)

    # Adding members conditon
    if team.member_ids:
        members = db.query(User).filter(User.id.in_(team.member_ids)).all()
        if len(members) != len(team.member_ids):
            return None, "One of the user IDs are invalid"
        new_team.members.extend(members)
        db.commit()

    return new_team, None

# getting a single team
def get_team(db: Session, team_id: int):
    return db.query(Team).filter(Team.id == team_id).first()

# updating the 
def update_team_members(db: Session, team_id: int, new_member_ids: list[int]):
    # Fetch the team
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        return None, "Team not found"

    # validation
    new_members = db.query(User).filter(User.id.in_(new_member_ids)).all()
    if len(new_members) != len(new_member_ids):
        return None, "One of the user IDs are invalid"

    # Add  new members
    team.members.extend(new_members)
    db.commit()

    return team, None