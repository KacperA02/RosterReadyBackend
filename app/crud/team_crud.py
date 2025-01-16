from sqlalchemy.orm import Session
from models.team_model import Team
from schemas.team_schema import TeamCreate

def create_team(db: Session, team: TeamCreate):
    new_team = Team(name=team.name, employer_id=team.employer_id)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team

def get_team(db: Session, team_id: int):
    return db.query(Team).filter(Team.id == team_id).first()

