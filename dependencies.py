from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from taskmaster import crud, models


def ensure_team_membership(team_id: str, user_id: str, db: Session) -> None:
    is_member = (
        db.query(models.user_team)
        .filter(models.user_team.c.team_id == team_id, models.user_team.c.user_id == user_id)
        .first()
    )
    if not is_member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not a team member")


def get_task_with_access_or_404(task_id: str, user_id: str, db: Session) -> models.Task:
    task = crud.get_task_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    ensure_team_membership(str(project.team_id), user_id, db)
    return task
