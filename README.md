
# Taskmaster

Operational task management system with:
- FastAPI backend
- PostgreSQL database via SQLAlchemy
- Single-page frontend served by FastAPI
- Drag and drop board
- Comments and attachments on tasks

## Quick Start

From repository root:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn taskmaster.main:app --reload
```

From `taskmaster` directory:

```bash
python -m venv ..\.venv
..\.venv\Scripts\activate
pip install -r ..\requirements.txt
uvicorn taskmaster.main:app --reload --app-dir ..
```

Open:
- UI: http://127.0.0.1:8000/frontend
- API docs: http://127.0.0.1:8000/docs

## Features

- Authentication: register, login, logout
- Teams and projects
- Task CRUD
- Task status workflow: open, in_progress, completed
- Search, filters, sorting, pagination
- Drag and drop between columns
- Comments on tasks
- File attachments on tasks
- Attachment preview support in UI (image, pdf, txt)

## Project Structure

- taskmaster/: Main backend app (includes frontend/)
- taskmaster/frontend/: HTML, CSS, JavaScript UI
- app/: Additional app package in workspace

## Requirements

- Python 3.10+
- PostgreSQL

Install Python dependencies from the generated requirements file:

```bash
pip install -r requirements.txt
```

If you are inside the `taskmaster` folder, use:

```bash
pip install -r ..\requirements.txt
```

Dependency lockfile notes:
- The pinned package list is in `requirements.txt` at the workspace root.
- To refresh it from the current environment:

```bash
python -m pip freeze > requirements.txt
```

## Environment Setup

Create file: taskmaster/.env

Example:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/taskdb
SECRET_KEY=replace_with_a_long_random_secret
UPLOAD_DIR=taskmaster/uploads
```

Notes:
- SECRET_KEY is required. App startup fails without it.
- Upload directory is auto-created at startup.

## Run the App

From workspace root:

```bash
uvicorn taskmaster.main:app --reload
```

Open in browser:
- UI: http://127.0.0.1:8000/frontend
- API docs: http://127.0.0.1:8000/docs

## How to Use Comments and Attachments

1. Open any task card (or click Details).
2. In Task Details and Edit modal:
   - Comments section: write text and click Add Comment.
   - Attachments section: choose file and click Upload File.
3. Existing comments and attachments appear in the same modal.
4. Attachment actions:
   - View: inline preview for image/pdf/txt
   - Open: open in new tab
   - Download: save locally

Attachment limits from backend config:
- Max size: 5 MB
- Allowed types: image/png, image/jpeg, application/pdf, text/plain

## Sorting Behavior

Sort dropdown options:
- Created
- Due Date
- Title

Behavior:
- Created sorts descending
- Due Date and Title sort ascending
- Sorting is applied through backend query parameters

## Troubleshooting

- Login fails with could not validate credentials:
  - Ensure SECRET_KEY is set
  - Ensure token is not stale; try logging in again

- Comments or attachments fail:
  - Ensure task is opened in edit/details mode
  - Ensure file type and size are allowed

- Database connection errors:
  - Verify DATABASE_URL
  - Ensure PostgreSQL is running

## Development Notes

- Frontend is a single file app in taskmaster/frontend/index.html.
- Backend auto-creates tables on startup via SQLAlchemy metadata.
- Uploaded files are served from /uploads.


