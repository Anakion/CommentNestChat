from fastapi import APIRouter, Request, Response
from src.services.captcha import CaptchaService

router = APIRouter(prefix="/captcha", tags=["captcha"])

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