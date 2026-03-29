import uuid
from pathlib import Path
from typing import List, cast

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from taskmaster import auth, crud, models, schemas
from taskmaster.config import ALLOWED_ATTACHMENT_TYPES, MAX_ATTACHMENT_SIZE, UPLOAD_DIR
from taskmaster.database import get_db
from taskmaster.dependencies import get_task_with_access_or_404

router = APIRouter(tags=["attachments"])


@router.post("/tasks/{task_id}/attachments/", response_model=schemas.AttachmentOut, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    task_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    get_task_with_access_or_404(task_id, cast(str, current_user.id), db)

    if file.content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    extension = Path(file.filename or "upload.bin").suffix
    safe_name = f"{uuid.uuid4().hex}{extension}"
    save_path = UPLOAD_DIR / safe_name

    size = 0
    chunk_size = 1024 * 1024
    try:
        with save_path.open("wb") as out_file:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                size += len(chunk)
                if size > MAX_ATTACHMENT_SIZE:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

                out_file.write(chunk)
    except Exception:
        if save_path.exists():
            save_path.unlink()
        raise
    finally:
        await file.close()

    return crud.create_attachment(
        db,
        file_name=file.filename or safe_name,
        file_url=f"/uploads/{safe_name}",
        file_size=size,
        uploaded_by_id=cast(str, current_user.id),
        task_id=task_id,
    )


@router.get("/tasks/{task_id}/attachments/", response_model=List[schemas.AttachmentOut])
def get_attachments(task_id: str, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    get_task_with_access_or_404(task_id, cast(str, current_user.id), db)
    return crud.list_task_attachments(db, task_id)


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    attachment = crud.get_attachment_by_id(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")

    task = get_task_with_access_or_404(cast(str, attachment.task_id), cast(str, current_user.id), db)
    if str(task.creator_id) != str(current_user.id) and str(attachment.uploaded_by_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete attachment")

    disk_path = UPLOAD_DIR / Path(str(attachment.file_url)).name
    if disk_path.exists():
        disk_path.unlink()

    crud.delete_attachment(db, attachment)
    return None
