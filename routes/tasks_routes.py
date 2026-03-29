from datetime import datetime
from typing import Optional, cast

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from taskmaster import auth, crud, models, schemas
from taskmaster.database import get_db
from taskmaster.dependencies import ensure_team_membership, get_task_with_access_or_404

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    user_id = cast(str, current_user.id)
    ensure_team_membership(str(project.team_id), user_id, db)

    if task.assignee_id:
        assignee = crud.get_user_by_id(db, task.assignee_id)
        if not assignee:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
        ensure_team_membership(str(project.team_id), task.assignee_id, db)

    return crud.create_task(db=db, task=task, creator_id=user_id)


@router.get("/", response_model=schemas.TaskListResponse)
def read_tasks(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    status: Optional[models.TaskStatus] = None,
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    q: Optional[str] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    tasks, total = crud.get_tasks(
        db,
        user_id=cast(str, current_user.id),
        skip=skip,
        limit=limit,
        status=status,
        project_id=project_id,
        assignee_id=assignee_id,
        creator_id=creator_id,
        q=q,
        due_before=due_before,
        due_after=due_after,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {"items": tasks, "total": total, "skip": skip, "limit": limit}


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    return get_task_with_access_or_404(task_id, cast(str, current_user.id), db)


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def patch_task(
    task_id: str,
    payload: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = get_task_with_access_or_404(task_id, cast(str, current_user.id), db)

    if payload.assignee_id:
        project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
        ensure_team_membership(str(project.team_id), payload.assignee_id, db)

    return crud.update_task(db, task, payload)


@router.patch("/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    return crud.update_task(db, task, schemas.TaskUpdate(status=models.TaskStatus.COMPLETED))


@router.patch("/{task_id}/assign/{assignee_id}", response_model=schemas.TaskOut)
def assign_task(
    task_id: str,
    assignee_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    task = get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    assignee = crud.get_user_by_id(db, assignee_id)
    if not assignee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")

    project = db.query(models.Project).filter(models.Project.id == task.project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    ensure_team_membership(str(project.team_id), assignee_id, db)

    return crud.update_task(db, task, schemas.TaskUpdate(assignee_id=assignee_id))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    task = get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    crud.delete_task(db, task)
    return None
