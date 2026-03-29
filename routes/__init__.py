from taskmaster.routes.auth_routes import router as auth_router
from taskmaster.routes.users_routes import router as users_router
from taskmaster.routes.tasks_routes import router as tasks_router
from taskmaster.routes.teams_routes import router as teams_router
from taskmaster.routes.projects_routes import router as projects_router
from taskmaster.routes.comments_routes import router as comments_router
from taskmaster.routes.attachments_routes import router as attachments_router

__all__ = [
    "auth_router",
    "users_router",
    "tasks_router",
    "teams_router",
    "projects_router",
    "comments_router",
    "attachments_router",
]
