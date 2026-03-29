from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskmaster import auth, crud, models, schemas
from taskmaster.database import get_db
from taskmaster.dependencies import get_task_with_access_or_404

router = APIRouter(tags=["comments"])


@router.post("/tasks/{task_id}/comments/", response_model=schemas.CommentOut, status_code=201)
def add_comment(
    task_id: str,
    payload: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    return crud.create_comment(db, task_id, cast(str, current_user.id), payload)


@router.get("/tasks/{task_id}/comments/", response_model=List[schemas.CommentOut])
def get_comments(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    return crud.list_task_comments(db, task_id)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    comment = crud.get_comment_by_id(db, comment_id)
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")

    task = get_task_with_access_or_404(cast(str, comment.task_id), cast(str, current_user.id), db)
    if str(task.creator_id) != str(current_user.id) and str(comment.author_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete comment")

    crud.delete_comment(db, comment)
    return None
