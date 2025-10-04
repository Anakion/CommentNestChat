from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.db.session import get_db
from src.repositories.comment_repo import CommentRepository
from src.services.comment import CommentService
from src.services.file_service import FileService
from src.services.redis_service import RedisService
from src.services.validation_service import ValidationService
from src.use_cases.create_comment_command import CreateCommentCommand


async def get_comment_repository(
    session: AsyncSession = Depends(get_db),
) -> CommentRepository:
    return CommentRepository(session=session)


async def get_comment_service(
    comment_repo: CommentRepository = Depends(get_comment_repository),
) -> CommentService:
    return CommentService(
        repository=comment_repo,
        settings=Settings(),
    )

def get_validation_service():
    return ValidationService()

def get_file_service():
    return FileService()


def get_create_comment_command(
    comment_service: CommentService = Depends(get_comment_service),
    validation_service: ValidationService = Depends(get_validation_service),
    file_service: FileService = Depends(get_file_service)
) -> CreateCommentCommand:
    return CreateCommentCommand(comment_service, validation_service, file_service)

