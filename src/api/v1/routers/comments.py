import json
import os
from http.client import HTTPException
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query, Form, UploadFile, File
from fastapi.encoders import jsonable_encoder
from starlette.requests import Request
from starlette.responses import FileResponse

from src.core.websocket import manager
from src.dependecy import get_comment_service
from src.schemas.comment import CommentResponseSchema, CommentCreateSchema
from src.services.comment import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


# @router.post("/", response_model=CommentResponseSchema)
# async def create_comment(
#     payload: CommentCreateSchema,
#     service: Annotated[CommentService, Depends(get_comment_service)],
# ):
#     new_comment = await service.create_comment(payload)
#
#     # Преобразуем модель в dict для фронта
#     comment_dict = jsonable_encoder(CommentResponseSchema.model_validate(new_comment))
#     print("Отправляем новый комментарий:", comment_dict)
#
#     # Рассылаем всем подключённым клиентам
#     await manager.broadcast_new_comment(comment_dict)
#
#     print("Broadcasted new_comment:", new_comment.id)
#     return new_comment


# @router.post("/", response_model=CommentResponseSchema)
# async def create_comment(
#         service: Annotated[CommentService, Depends(get_comment_service)],
#         user_name: str = Form(...),
#         email: str = Form(...),
#         home_page: Optional[str] = Form(None),
#         captcha: str = Form(...),
#         text: str = Form(...),
#         parent_id: Optional[int] = Form(None),
#         image: Optional[UploadFile] = File(None),
#         text_file: Optional[UploadFile] = File(None),
# ):
#     # Валидируем через схему
#     payload = CommentCreateSchema(
#         user_name=user_name,
#         email=email,
#         home_page=home_page,
#         captcha=captcha,
#         text=text,
#         parent_id=parent_id
#     )
#
#     # Обрабатываем файлы
#     file_path = None
#     file_type = None
#     image_w = None
#     image_h = None
#
#     if image and image.file:
#         file_path, file_type, image_w, image_h = await service.save_image(image)
#     elif text_file and text_file.file:
#         file_path, file_type = await service.save_text_file(text_file)
#
#     # Создаем комментарий
#     new_comment = await service.create_comment(
#         comment_data=payload,
#         file_path=file_path,
#         file_type=file_type,
#         image_w=image_w,
#         image_h=image_h
#     )
#
#     # Преобразуем для фронта
#     comment_dict = jsonable_encoder(CommentResponseSchema.model_validate(new_comment))
#     print("Отправляем новый комментарий с файлом:", comment_dict)
#
#     # Рассылаем всем подключённым клиентам
#     await manager.broadcast_new_comment(comment_dict)
#
#     return new_comment


@router.post("/", response_model=CommentResponseSchema)
async def create_comment(
        request: Request,
        service: Annotated[CommentService, Depends(get_comment_service)],
):
    try:
        print("🎯 === REACHED THE FUNCTION! ===")

        # Парсим FormData вручную
        form_data = await request.form()

        print("🔹 Form data keys:", list(form_data.keys()))

        # Достаем поля вручную
        user_name = form_data.get("user_name")
        email = form_data.get("email")
        home_page = form_data.get("home_page")
        captcha = form_data.get("captcha")
        text = form_data.get("text")
        parent_id = form_data.get("parent_id")

        # ФИКС: преобразуем parent_id
        if parent_id == '':
            parent_id = None
        elif parent_id:
            try:
                parent_id = int(parent_id)
            except ValueError:
                parent_id = None

        print("🔹 user_name:", user_name)
        print("🔹 email:", email)
        print("🔹 home_page:", home_page)
        print("🔹 captcha:", captcha)
        print("🔹 text:", text)
        print("🔹 parent_id:", parent_id, type(parent_id))

        # Валидация
        import re

        # Валидация имени
        if not re.match(r"^[a-zA-Z0-9]{1,60}$", user_name):
            raise HTTPException(422, "Invalid user name format")

        # Валидация email
        if "@" not in email:
            raise HTTPException(422, "Invalid email format")

        # Валидация CAPTCHA
        if not re.match(r"^[a-zA-Z0-9]{1,10}$", captcha):
            raise HTTPException(422, "Invalid CAPTCHA format")

        # Валидация HTML тегов
        allowed_tags = ["a", "code", "i", "strong"]
        tags = re.findall(r"</?(\w+)", text)
        for tag in tags:
            if tag not in allowed_tags:
                raise HTTPException(422, f"HTML tag <{tag}> is not allowed")

        # Обрабатываем файлы (объявляем переменные ЗАРАНЕЕ)
        file_path = None
        file_type = None
        image_w = None
        image_h = None

        # Получаем файлы
        image = form_data.get("image")
        text_file = form_data.get("text_file")

        print("🔹 image:", image.filename if image else None)
        print("🔹 text_file:", text_file.filename if text_file else None)

        if image and image.file:
            print("📁 Processing image...")
            file_path, file_type, image_w, image_h = await service.save_image(image)
            print("✅ Image saved:", file_path)
        elif text_file and text_file.file:
            print("📁 Processing text file...")
            file_path, file_type = await service.save_text_file(text_file)
            print("✅ Text file saved:", file_path)

        # Создаем Pydantic модель
        payload = CommentCreateSchema(
            user_name=user_name,
            email=email,
            home_page=home_page,
            captcha=captcha,
            text=text,
            parent_id=parent_id
        )

        # Создаем комментарий через service
        print("🚀 Creating comment...")
        new_comment = await service.create_comment(
            comment_data=payload,
            file_path=file_path,
            file_type=file_type,
            image_w=image_w,
            image_h=image_h
        )

        # Преобразуем для фронта
        comment_dict = jsonable_encoder(CommentResponseSchema.model_validate(new_comment))
        print("📤 Sending new comment:", comment_dict)

        # Рассылаем всем подключённым клиентам
        await manager.broadcast_new_comment(comment_dict)

        print("🎊 COMMENT CREATED SUCCESSFULLY!")
        return new_comment

    except Exception as e:
        print("💥 UNEXPECTED ERROR:", str(e))
        raise e


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