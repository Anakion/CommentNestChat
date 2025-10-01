from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Settings
from src.db.session import get_db
from src.repositories.comment_repo import CommentRepository
from src.services.comment import CommentService


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



