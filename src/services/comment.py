import io
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException, UploadFile

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

    async def create_comment(
            self,
            comment_data: CommentCreateSchema,
            file_path: Optional[str] = None,
            file_type: Optional[str] = None,
            image_w: Optional[int] = None,
            image_h: Optional[int] = None
    ) -> Comments:
        """Создает комментарий с файлами"""
        # Добавляем файловые поля в данные
        comment_dict = comment_data.model_dump()
        comment_dict.update({
            "file_path": file_path,
            "file_type": file_type,
            "image_w": image_w,
            "image_h": image_h
        })

        return await self.repository.create_comment(comment_dict)

    async def save_image(self, image: UploadFile) -> tuple[str, str, int, int]:
        """Сохраняет и ресайзит изображение, возвращает (path, type, width, height)"""
        import os
        import uuid
        from PIL import Image

        os.makedirs("uploads", exist_ok=True)

        # Определяем тип файла
        file_ext = os.path.splitext(image.filename)[1].lower()
        file_type = "image"

        # Генерируем имя
        filename = f"{uuid.uuid4()}{file_ext}"
        file_path = f"uploads/{filename}"

        # Обрабатываем изображение
        image_data = await image.read()

        with Image.open(io.BytesIO(image_data)) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Получаем оригинальные размеры
            orig_width, orig_height = img.size

            # Ресайз до 320x240 с сохранением пропорций
            img.thumbnail((320, 240), Image.Resampling.LANCZOS)

            # Получаем новые размеры
            new_width, new_height = img.size

            # Сохраняем
            img.save(file_path, optimize=True, quality=85)

        return file_path, file_type, new_width, new_height

    async def save_text_file(self, text_file: UploadFile) -> tuple[str, str]:
        """Сохраняет текстовый файл, возвращает (path, type)"""
        import os
        import uuid

        if not text_file.filename.lower().endswith('.txt'):
            raise ValueError("Only TXT files allowed")

        os.makedirs("uploads", exist_ok=True)

        # Проверяем размер
        file_data = await text_file.read()
        if len(file_data) > 100 * 1024:
            raise ValueError("Text file too large (max 100KB)")

        file_type = "text"
        filename = f"{uuid.uuid4()}.txt"
        file_path = f"uploads/{filename}"

        # Сохраняем
        with open(file_path, 'wb') as f:
            f.write(file_data)

        return file_path, file_type













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
