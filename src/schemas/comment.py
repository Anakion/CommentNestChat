from datetime import datetime

from pydantic import BaseModel, EmailStr, HttpUrl, validator, field_validator
from typing import Optional, List
import re

USERNAME_REGEX = r"^[a-zA-Z0-9]{1,60}$"
CAPTCHA_REGEX = r"^[a-zA-Z0-9]{1,10}$"
ALLOWED_TAGS = ["a", "code", "i", "strong"]


class CommentCreateSchema(BaseModel):
    user_name: str
    email: str
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
        from html.parser import HTMLParser

        class AllowedHTMLValidator(HTMLParser):
            def __init__(self):
                super().__init__()
                self.allowed_tags = ALLOWED_TAGS
                self.tag_stack = []
                self.errors = []

            def handle_starttag(self, tag, attrs):
                if tag not in self.allowed_tags:
                    self.errors.append(f"Tag <{tag}> is not allowed")
                    return

                # Проверяем атрибуты для тега <a>
                if tag == 'a':
                    allowed_attrs = ['href', 'title']
                    for attr, val in attrs:
                        if attr not in allowed_attrs:
                            self.errors.append(f"Attribute '{attr}' not allowed in <a> tag")

                self.tag_stack.append(tag)

            def handle_endtag(self, tag):
                if not self.tag_stack:
                    self.errors.append(f"Closing tag </{tag}> without opening tag")
                    return

                if self.tag_stack[-1] != tag:
                    self.errors.append(f"Unclosed tag <{self.tag_stack[-1]}>")

                self.tag_stack.pop()

            def check_unclosed_tags(self):
                if self.tag_stack:
                    for tag in self.tag_stack:
                        self.errors.append(f"Unclosed tag <{tag}>")

        # Запускаем валидацию
        validator = AllowedHTMLValidator()
        validator.feed(value)
        validator.check_unclosed_tags()

        if validator.errors:
            raise ValueError("; ".join(validator.errors))

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
