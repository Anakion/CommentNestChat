from datetime import datetime

from pydantic import BaseModel, EmailStr, HttpUrl, validator, field_validator
from typing import Optional, List
import re

USERNAME_REGEX = r"^[a-zA-Z0-9]{1,60}$"
CAPTCHA_REGEX = r"^[a-zA-Z0-9]{1,10}$"
ALLOWED_TAGS = ["a", "code", "i", "strong"]


class CommentCreateSchema(BaseModel):
    user_name: str
    email: EmailStr
    home_page: Optional[str] = None
    captcha: str
    text: str
    parent_id: Optional[int] = None

    # Проверка User name
    @field_validator("user_name")
    def validate_user_name(cls, value):
        if not re.match(USERNAME_REGEX, value):
            raise ValueError(
                "User name must be between 1 and 60 characters long and contain only **English letters and numbers**"
            )
        return value

    # Проверка CAPTCHA
    @field_validator("captcha")
    def validate_captcha(cls, value):
        if not re.match(CAPTCHA_REGEX, value):
            raise ValueError(
                "CAPTCHA must be between 1 and 10 characters long and contain only letters and numbers"
            )
        return value

    # Проверка текста на разрешенные HTML-теги
    @field_validator("text")
    def validate_text(cls, value):
        tags = re.findall(r"</?(\w+)", value)
        for tag in tags:
            if tag not in ALLOWED_TAGS:
                raise ValueError(f"HTML tag <{tag}> is not allowed")
        return value

        # Добавляем валидацию для home_page

    @field_validator("home_page")
    def validate_home_page(cls, value):
        if not value:  # Это покрывает None, "", и другие "false" значения
            return None

        # Проверяем что value - строка и начинается с http/https
        if isinstance(value, str) and not value.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")

        return value


class CommentResponseSchema(BaseModel):
    id: int
    user_name: str
    email: EmailStr
    home_page: Optional[HttpUrl] = None
    text: str
    parent_id: Optional[int] = None
    created_at: datetime
    file_path: Optional[str] = None
    file_type: Optional[str] = None
    image_w: Optional[int] = None
    image_h: Optional[int] = None
    replies: List["CommentResponseSchema"] = []

    class Config:
        from_attributes = True

        """позволяет сериализовать SQLAlchemy 
        объекты (или любые Python-объекты с атрибутами) 
        напрямую в JSON через Pydantic

        Можете читать данные не только из словарей, 
        но и из объектов с атрибутами, 
        например из SQLAlchemy моделей"""
