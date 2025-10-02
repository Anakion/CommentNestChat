from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder

from src.models.comment import Comments
from src.schemas.comment import CommentCreateSchema, CommentResponseSchema


class CreateCommentCommand:
    def __init__(self, comment_service, validation_service, file_service):
        self.comment_service = comment_service
        self.validation_service = validation_service
        self.file_service = file_service

    async def execute(self, form_data) -> Comments:
        try:
            # 1. Разделяем данные ДО валидации
            text_fields = {}
            files = {}

            for key in form_data.keys():
                value = form_data.get(key)

                if hasattr(value, 'filename') and value.filename:
                    files[key] = value
                else:
                    text_fields[key] = value

            # 2. Валидация ТОЛЬКО текстовых полей
            clean_data = await self.validation_service.validate_comment_data(text_fields)

            # 3. Обработка файлов (передаем ТОЛЬКО файлы)
            file_info = await self.file_service.process_uploaded_files(files, self.comment_service)

            # 4. Создание комментария
            payload = CommentCreateSchema(**clean_data)
            comment = await self.comment_service.create_comment(payload, **file_info)

            # 5. Нотификации
            await self._notify_clients(comment)

            print("🎊 COMMENT CREATED SUCCESSFULLY!")
            return comment

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, "Internal server error")

    async def _notify_clients(self, comment):
        from src.api.v1.routers.comments import manager  # импорт здесь чтобы избежать circular import
        comment_dict = jsonable_encoder(CommentResponseSchema.model_validate(comment))
        await manager.broadcast_new_comment(comment_dict)
