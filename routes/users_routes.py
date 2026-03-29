from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskmaster import auth, crud, models, schemas
from taskmaster.database import get_db

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=schemas.UserOut)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.patch("/me", response_model=schemas.UserOut)
def update_my_profile(
    payload: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if payload.username and payload.username != current_user.username:
        if crud.get_user_by_username(db, payload.username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    if payload.email and payload.email != current_user.email:
        if crud.get_user_by_email(db, payload.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    return crud.update_user(db, current_user, payload)
