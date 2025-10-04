import uuid
from typing import Annotated

from fastapi import APIRouter, Request, Response, Depends, HTTPException
from src.services.captcha import CaptchaService
from src.services.redis_service import RedisService

router = APIRouter(prefix="/captcha", tags=["captcha"])

# ⚠️ ОБЪЯВЛЯЕМ DEPENDENCY ПРЯМО ЗДЕСЬ (быстрое решение)
async def get_redis_service() -> RedisService:
    return RedisService()

# ⚠️ ВРЕМЕННОЕ ХРАНИЛИЩЕ В ПАМЯТИ
captcha_storage = {"current": None}


@router.get("/")
async def get_captcha(request: Request):
    captcha_service = CaptchaService()
    captcha_text, image_buffer = captcha_service.generate_captcha()

    print(f"🔐 BEFORE: {captcha_storage['current']}")  # ← что было ДО
    captcha_storage["current"] = captcha_text  # type: ignore
    print(f"🔐 AFTER: {captcha_storage['current']}")  # ← что стало ПОСЛЕ

    return Response(
        content=image_buffer.getvalue(),
        media_type="image/png"
    )

# @router.get("/")
# async def get_captcha(
#         request: Request,
#         redis_service: Annotated[RedisService, Depends(get_redis_service)],
# ):
#     # Диагностика: что пришло в cookies
#     print(f"🍪 ALL COOKIES: {dict(request.cookies)}")
#
#     session_id = request.cookies.get("session_id")
#     is_new_session = False
#
#     if not session_id:
#         session_id = str(uuid.uuid4())
#         is_new_session = True
#         print(f"🆔 Created NEW session_id: {session_id}")
#     else:
#         print(f"🆔 Using EXISTING session_id: {session_id}")
#
#     # Проверим, есть ли уже капча
#     existing_captcha = await redis_service.get_captcha(session_id)
#     if existing_captcha:
#         print(f"♻️ Overwriting existing CAPTCHA for {session_id[:8]}")
#     else:
#         print(f"✨ Creating new CAPTCHA for {session_id[:8]}")
#
#     # Генерация капчи
#     captcha_service = CaptchaService()
#     captcha_text, image_buffer = captcha_service.generate_captcha()
#
#     # Сохранение в Redis (перезапишет, если ключ есть)
#     await redis_service.store_captcha(session_id, captcha_text)
#
#     print(f"🔐 CAPTCHA for {session_id[:8]}: {captcha_text}")
#     print(f"📊 Redis keys: {await redis_service.redis_client.keys('captcha:*')}")
#
#     # Создаём Response с изображением
#     response = Response(content=image_buffer.getvalue(), media_type="image/png")
#
#     # Устанавливаем cookie ТОЛЬКО если сессия новая
#     if is_new_session:
#         response.set_cookie(
#             key="session_id",
#             value=session_id,
#             httponly=True,
#             max_age=3600,
#             samesite="lax",
#         )
#         print(f"🍪 SET COOKIE: {session_id}")
#
#     return response


