import os
from http.client import HTTPException
from typing import Annotated, List

from fastapi import APIRouter, Depends
from starlette.requests import Request
from starlette.responses import FileResponse

from src.core.websocket import manager
from src.dependecy import get_comment_service, get_create_comment_command
from src.schemas.comment import CommentResponseSchema
from src.services.comment import CommentService
from src.use_cases.create_comment_command import CreateCommentCommand

router = APIRouter(prefix="/comments", tags=["comments"])


@router.post("/", response_model=CommentResponseSchema)
async def create_comment(
    request: Request,
    command: Annotated[CreateCommentCommand, Depends(get_create_comment_command)],
):
    form_data = await request.form()
    return await command.execute(form_data)


@router.get("/", response_model=List[CommentResponseSchema])
async def get_all_comments(
    service: Annotated[CommentService, Depends(get_comment_service)],
):
    return await service.get_all_comments()


@router.get("/files/{file_path:path}")
async def get_file(file_path: str):
    # file_path приходит как 'b122c957-8d09-49d1-a312-7b9b84d4fdcb.jpg'
    file_full_path = f"uploads/{file_path}"  # добавляем uploads/

    print(f"🔍 Looking for file: {file_full_path}")

    if not os.path.exists(file_full_path):
        print(f"❌ File not found: {file_full_path}")
        raise HTTPException()

    print(f"✅ File found: {file_full_path}")

    # Определяем Content-Type
    if file_path.lower().endswith(('.jpg', '.jpeg')):
        media_type = "image/jpeg"
    elif file_path.lower().endswith('.png'):
        media_type = "image/png"
    elif file_path.lower().endswith('.gif'):
        media_type = "image/gif"
    elif file_path.lower().endswith('.txt'):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"

    return FileResponse(file_full_path, media_type=media_type)