from typing import List, cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from taskmaster import auth, crud, models, schemas
from taskmaster.database import get_db
from taskmaster.dependencies import ensure_team_membership

router = APIRouter(tags=["teams"])


@router.get("/teams/mine", response_model=List[schemas.TeamOut])
def list_my_teams(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return (
        db.query(models.Team)
        .join(models.user_team, models.user_team.c.team_id == models.Team.id)
        .filter(models.user_team.c.user_id == cast(str, current_user.id))
        .order_by(models.Team.name.asc())
        .all()
    )


@router.post("/teams/", response_model=schemas.TeamOut, status_code=status.HTTP_201_CREATED)
def create_new_team(
    team: schemas.TeamCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return crud.create_team(db=db, team=team, owner_id=cast(str, current_user.id))


@router.post("/teams/{team_id}/invite/{username}", response_model=schemas.TeamInvitationOut, status_code=status.HTTP_201_CREATED)
def invite_member_to_team(
    team_id: str,
    username: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can invite")

    new_member = crud.get_user_by_username(db, username=username)
    if not new_member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    pending = crud.get_pending_invitation(db, team_id, cast(str, new_member.id))
    if pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pending invitation already exists")

    if new_member in team.members:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already in the team")

    return crud.create_invitation(db, team_id, cast(str, new_member.id), cast(str, current_user.id))


@router.get("/teams/{team_id}/invitations", response_model=List[schemas.TeamInvitationOut])
def get_team_invitations(
    team_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    if str(team.owner_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can view invitations")

    return crud.list_team_invitations(db, team_id)


@router.post("/invitations/{invitation_id}/accept", response_model=schemas.TeamInvitationOut)
def accept_team_invitation(
    invitation_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    invitation = crud.get_invitation_by_id(db, invitation_id)
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if str(invitation.invited_user_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You cannot accept this invitation")

    if str(invitation.status) != str(models.InvitationStatus.PENDING):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation is no longer pending")

    return crud.accept_invitation(db, invitation)


@router.get("/teams/{team_id}", response_model=schemas.TeamOut)
def get_team(team_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    team = db.query(models.Team).filter(models.Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")
    ensure_team_membership(team_id, cast(str, current_user.id), db)
    return team
