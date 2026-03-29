from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskmaster import auth, models, schemas
from taskmaster.database import get_db
from taskmaster.dependencies import ensure_team_membership

router = APIRouter(tags=["projects"])


@router.post("/projects/", response_model=schemas.ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    team = db.query(models.Team).filter(models.Team.id == project.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    if current_user not in team.members:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You must be part of the team")

    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/teams/{team_id}/projects", response_model=List[schemas.ProjectOut])
def list_team_projects(team_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    ensure_team_membership(team_id, str(current_user.id), db)
    return db.query(models.Project).filter(models.Project.team_id == team_id).all()
