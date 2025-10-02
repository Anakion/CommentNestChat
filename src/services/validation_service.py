import re
from fastapi import HTTPException


class ValidationService:
    def __init__(self):
        self.allowed_tags = ["a", "code", "i", "strong"]

    async def validate_comment_data(self, form_data) -> dict:
            # Преобразуем FormData в dict
        data_dict = {}
        for key in form_data.keys():
            data_dict[key] = form_data.get(key)

        user_name = form_data.get("user_name")
        email = form_data.get("email")
        home_page = form_data.get("home_page")
        captcha = form_data.get("captcha")
        text = form_data.get("text")
        parent_id = form_data.get("parent_id")

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
        tags = re.findall(r"</?(\w+)", text)
        for tag in tags:
            if tag not in self.allowed_tags:
                raise HTTPException(422, f"HTML tag <{tag}> is not allowed")

        # Преобразуем parent_id
        if parent_id == '':
            parent_id = None
        elif parent_id:
            try:
                parent_id = int(parent_id)
            except ValueError:
                parent_id = None

        return {
            "user_name": user_name,
            "email": email,
            "home_page": home_page,
            "captcha": captcha,
            "text": text,
            "parent_id": parent_id
        }