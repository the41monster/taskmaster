from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from taskmaster import models
from taskmaster.config import UPLOAD_DIR, ensure_upload_dir
from taskmaster.database import engine
from taskmaster.routes import (
    attachments_router,
    auth_router,
    comments_router,
    projects_router,
    tasks_router,
    teams_router,
    users_router,
)

app = FastAPI(title="Task Management System")

models.Base.metadata.create_all(bind=engine)
ensure_upload_dir()
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/", include_in_schema=False)
def root_redirect():
    if FRONTEND_DIR.exists():
        return RedirectResponse(url="/frontend")
    return {"message": "Taskmaster API is running"}

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(tasks_router)
app.include_router(teams_router)
app.include_router(projects_router)
app.include_router(comments_router)
app.include_router(attachments_router)
