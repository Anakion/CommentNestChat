from dataclasses import dataclass
from fastapi import HTTPException

from src.core.config import Settings
from src.models.comment import Comments
from src.repositories.comment_repo import CommentRepository
from src.schemas.comment import CommentCreateSchema, CommentResponseSchema


@dataclass
class CommentService:
    repository: CommentRepository
    settings: Settings

    async def get_all_comments(self) -> list[Comments]:
        """Получить все комментарии с вложенной структурой"""
        return await self.repository.get_all_comments_with_replies()

    async def create_comment(self, payload: CommentCreateSchema) -> CommentResponseSchema:
        """Создать новый комментарий"""
        db_comment = await self.repository.create_comment(payload)
        return CommentResponseSchema.model_validate(db_comment)

    # async def create_comment(self, comment: CommentCreateSchema) -> Comments:
    #     # Если user_name пустой или состоит только из пробелов
    #     if not comment.user_name or not comment.user_name.strip():
    #         raise HTTPException(status_code=400, detail="User name is required")
    #
    #     # Если текст пустой или состоит только из пробелов
    #     if not comment.text.strip():
    #         raise HTTPException(status_code=400, detail="Text is required")
    #
    #     if comment.parent_id:
    #         # Получаем родительский комментарий из репозитория
    #         parent_comment = await self.repository.get_comment_by_id(comment.parent_id)
    #         # Если такого комментария нет
    #         if not parent_comment:
    #             raise HTTPException(status_code=404, detail="Parent comment not found")
    #
    #     try:
    #         # Создаем комментарий в базе
    #         created_comment = await self.repository.create_comment(comment)
    #
    #         # Отправляем новый комментарий через WebSocket
    #         await self._broadcast_new_comment(created_comment)
    #
    #         return created_comment
    #     except Exception as e:
    #         raise HTTPException(status_code=400, detail=str(e))
    #
    # async def _broadcast_new_comment(self, comment: Comments):
    #     """Отправляет новый комментарий всем подключенным клиентам"""
    #     # Преобразуем комментарий в словарь
    #     comment_dict = {
    #         "id": str(comment.id),
    #         "user_name": comment.user_name,
    #         "text": comment.text,
    #         "parent_id": str(comment.parent_id) if comment.parent_id else None,
    #         "created_at": comment.created_at.isoformat(),
    #     }
    #
    #     # Отправляем через менеджер WebSocket
    #     await manager.broadcast_comment(comment_dict)
    #
    # async def list_comments(
    #     self,
    #     page: int = 1,
    #     per_page: int = 25,
    #     sort_by: str = "created_at",
    #     order: str = "desc",
    # ) -> list[Comments]:
    #     skip = (page - 1) * per_page
    #     return await self.repository.get_comments(
    #         skip=skip, limit=per_page, sort_by=sort_by, order=order
    #     )
    #
    # async def list_comments_with_replies(
    #     self,
    #     page: int = 1,
    #     per_page: int = 25,
    #     sort_by: str = "created_at",
    #     order: str = "desc",
    # ) -> list[Comments]:
    #     skip = (page - 1) * per_page
    #     roots = await self.repository.get_comments(
    #         skip=skip, limit=per_page, sort_by=sort_by, order=order
    #     )
    #
    #     # для каждого корневого комментария подтягиваем ответы рекурсивно
    #     for root in roots:
    #         root.replies = await self.repository.get_replies(root.id)
    #     return roots
