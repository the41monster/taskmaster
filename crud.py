from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, asc, desc
from datetime import datetime, timezone
from taskmaster import models, schemas, auth
from typing import Any, Optional, cast

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_id(db: Session, user_id: str):
    return db.query(models.User).filter(models.User.id == user_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pwd = auth.get_password_hash(user.password)
    db_user = models.User(
        username = user.username,
        email=user.email,
        fullname=user.fullname,
        hashed_password = hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, db_user: models.User, user: schemas.UserUpdate):
    db_user_any = cast(Any, db_user)
    if user.username is not None:
        db_user_any.username = cast(str, user.username)
    if user.email is not None:
        db_user_any.email = str(user.email)
    if user.fullname is not None:
        db_user_any.fullname = cast(str, user.fullname)
    if user.new_password:
        db_user_any.hashed_password = auth.get_password_hash(user.new_password)

    db.commit()
    db.refresh(db_user)
    return db_user

def get_tasks(
    db: Session,
    user_id: str,
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.TaskStatus] = None,
    project_id: Optional[str] = None,
    assignee_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    q: Optional[str] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    query = (
        db.query(models.Task)
        .join(models.Project, models.Task.project_id == models.Project.id)
        .join(models.user_team, models.user_team.c.team_id == models.Project.team_id)
        .filter(models.user_team.c.user_id == user_id)
        .options(joinedload(models.Task.creator), joinedload(models.Task.assignee))
    )

    if status:
        query = query.filter(models.Task.status == status)
    if project_id:
        query = query.filter(models.Task.project_id == project_id)
    if assignee_id:
        query = query.filter(models.Task.assignee_id == assignee_id)
    if creator_id:
        query = query.filter(models.Task.creator_id == creator_id)
    if due_before:
        query = query.filter(models.Task.due_date <= due_before)
    if due_after:
        query = query.filter(models.Task.due_date >= due_after)
    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(or_(models.Task.title.ilike(search_term), models.Task.description.ilike(search_term)))

    sort_columns = {
        "created_at": models.Task.created_at,
        "updated_at": models.Task.updated_at,
        "due_date": models.Task.due_date,
        "title": models.Task.title,
        "status": models.Task.status,
    }
    sort_column = sort_columns.get(sort_by, models.Task.created_at)
    order_func = desc if sort_order.lower() == "desc" else asc
    query = query.order_by(order_func(sort_column))

    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total

def create_task(db: Session, task: schemas.TaskCreate, creator_id: str):
    db_task = models.Task(
        **task.model_dump(),
        creator_id=creator_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def get_task_by_id(db: Session, task_id: str):
    return db.query(models.Task).filter(models.Task.id == task_id).first()


def update_task(db: Session, db_task: models.Task, task_update: schemas.TaskUpdate):
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, db_task: models.Task):
    db.delete(db_task)
    db.commit()

def update_task_status(db: Session, task_id: str, status: models.TaskStatus):
    db_task = db.query(models.Task).filter(models.Task.id==task_id).first()
    if db_task:
        setattr(db_task, "status", status)
        db.commit()
        db.refresh(db_task)
    return db_task

def create_team(db: Session, team: schemas.TeamCreate, owner_id: str):
    db_team = models.Team(**team.model_dump(), owner_id=owner_id)
    owner = db.query(models.User).filter(models.User.id==owner_id).first()
    if owner:
        db_team.members.append(owner)
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


def create_invitation(db: Session, team_id: str, invited_user_id: str, invited_by_id: str):
    invitation = models.TeamInvitation(
        team_id=team_id,
        invited_user_id=invited_user_id,
        invited_by_id=invited_by_id,
        status=models.InvitationStatus.PENDING,
    )
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    return invitation


def get_pending_invitation(db: Session, team_id: str, invited_user_id: str):
    return (
        db.query(models.TeamInvitation)
        .filter(
            models.TeamInvitation.team_id == team_id,
            models.TeamInvitation.invited_user_id == invited_user_id,
            models.TeamInvitation.status == models.InvitationStatus.PENDING,
        )
        .first()
    )


def list_team_invitations(db: Session, team_id: str):
    return (
        db.query(models.TeamInvitation)
        .filter(models.TeamInvitation.team_id == team_id)
        .order_by(models.TeamInvitation.created_at.desc())
        .all()
    )


def get_invitation_by_id(db: Session, invitation_id: str):
    return db.query(models.TeamInvitation).filter(models.TeamInvitation.id == invitation_id).first()


def accept_invitation(db: Session, invitation: models.TeamInvitation):
    invitation_any = cast(Any, invitation)
    invitation_any.status = models.InvitationStatus.ACCEPTED
    invitation_any.responded_at = datetime.now(timezone.utc)

    team = db.query(models.Team).filter(models.Team.id == invitation.team_id).first()
    user = db.query(models.User).filter(models.User.id == invitation.invited_user_id).first()
    if team and user:
        members = cast(Any, team.members)
        if user not in members:
            members.append(user)

    db.commit()
    db.refresh(invitation)
    return invitation


def create_comment(db: Session, task_id: str, author_id: str, payload: schemas.CommentCreate):
    comment = models.Comment(content=payload.content, task_id=task_id, author_id=author_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_task_comments(db: Session, task_id: str):
    return (
        db.query(models.Comment)
        .filter(models.Comment.task_id == task_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )


def get_comment_by_id(db: Session, comment_id: str):
    return db.query(models.Comment).filter(models.Comment.id == comment_id).first()


def delete_comment(db: Session, comment: models.Comment):
    db.delete(comment)
    db.commit()


def create_attachment(db: Session, file_name: str, file_url: str, file_size: int, uploaded_by_id: str, task_id: str):
    attachment = models.Attachment(
        file_name=file_name,
        file_url=file_url,
        file_size=file_size,
        uploaded_by_id=uploaded_by_id,
        task_id=task_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def list_task_attachments(db: Session, task_id: str):
    return (
        db.query(models.Attachment)
        .filter(models.Attachment.task_id == task_id)
        .order_by(models.Attachment.uploaded_at.desc())
        .all()
    )


def get_attachment_by_id(db: Session, attachment_id: str):
    return db.query(models.Attachment).filter(models.Attachment.id == attachment_id).first()


def delete_attachment(db: Session, attachment: models.Attachment):
    db.delete(attachment)
    db.commit()