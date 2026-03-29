import uuid
from sqlalchemy import Column, String, ForeignKey, Table, DateTime, Enum, Boolean, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from taskmaster.database import Base

def generate_uuid():
    return str(uuid.uuid4())

user_team = Table(
    "user_team",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("team_id", String, ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True),
)

class TaskStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class InvitationStatus(enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"

# TODO: Change to mapped column
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    fullname = Column(String)
    is_active = Column(Boolean, default=True)

    # Relationships
    teams = relationship("Team", secondary=user_team, back_populates="members")
    created_tasks = relationship("Task", foreign_keys="Task.creator_id", back_populates="creator")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    comments = relationship("Comment", back_populates="author")

class Team(Base):
    __tablename__ = "teams"
    
    id  = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    owner_id = Column(String, ForeignKey("users.id"), index=True)

    # Relationships
    members = relationship("User", secondary=user_team, back_populates="teams")
    projects = relationship("Project", back_populates="team", cascade="all, delete-orphan")

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(String)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), index=True)

    # Relationships
    team = relationship("Team", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, index=True, nullable=False)
    description = Column(String)
    due_date = Column(DateTime, index=True)
    status = Column(Enum(TaskStatus, native_enum=False), default=TaskStatus.OPEN, index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), index=True)

    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    creator_id = Column(String, ForeignKey("users.id"), index=True)
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)

    project = relationship("Project", back_populates="tasks")
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_task_project_status", "project_id", "status"),
        Index("idx_task_assignee_status", "assignee_id", "status"),
    )

class Comment(Base):
    __tablename__ = "comments"

    id = Column(String, primary_key=True, default=generate_uuid)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    author_id = Column(String, ForeignKey("users.id"), index=True)

    task = relationship("Task", back_populates="comments")
    author = relationship("User", back_populates="comments")

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String, primary_key=True, default=generate_uuid)
    file_name = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, server_default=func.now())
    uploaded_by_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(String, ForeignKey("tasks.id", ondelete="CASCADE"), index=True)

    task = relationship("Task", back_populates="attachments")


class TeamInvitation(Base):
    __tablename__ = "team_invitations"

    id = Column(String, primary_key=True, default=generate_uuid)
    team_id = Column(String, ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    invited_by_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(Enum(InvitationStatus, native_enum=False), default=InvitationStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now())
    responded_at = Column(DateTime)

    team = relationship("Team")
    invited_user = relationship("User", foreign_keys=[invited_user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_id])


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id = Column(String, primary_key=True, default=generate_uuid)
    token_hash = Column(String, unique=True, index=True, nullable=False)
    jti = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, server_default=func.now())