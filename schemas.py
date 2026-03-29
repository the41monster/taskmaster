from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from datetime import datetime
from taskmaster.models import TaskStatus, InvitationStatus

class UserBase(BaseModel):
    username: str
    email: EmailStr
    fullname: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    fullname: Optional[str] = None
    new_password: Optional[str] = None

class UserOut(UserBase):
    id: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.OPEN

class TaskCreate(TaskBase):
    project_id: str
    assignee_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[str] = None

class TaskOut(TaskBase):
    id: str
    creator_id: str
    project_id: str
    assignee_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    items: List[TaskOut]
    total: int
    skip: int
    limit: int

class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None

class TeamOut(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    owner_id: str
    members: List[UserOut] = []
    model_config = ConfigDict(from_attributes=True)

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str]
    team_id: str

class ProjectOut(BaseModel):
    id: str
    name: str
    team_id: str
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: str
    content: str
    task_id: str
    author_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AttachmentOut(BaseModel):
    id: str
    file_name: str
    file_url: str
    file_size: int
    uploaded_at: datetime
    uploaded_by_id: str
    task_id: str
    model_config = ConfigDict(from_attributes=True)


class TeamInvitationOut(BaseModel):
    id: str
    team_id: str
    invited_user_id: str
    invited_by_id: str
    status: InvitationStatus
    created_at: datetime
    responded_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class MessageOut(BaseModel):
    message: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None