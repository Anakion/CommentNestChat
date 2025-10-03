# services/captcha_service.py
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


class CaptchaService:
    def generate_captcha(self) -> tuple[str, BytesIO]:
        """Генерирует CAPTCHA: возвращает (текст, изображение)"""

        # 1. Генератор случайного текста
        length = 6
        characters = string.ascii_letters + string.digits
        captcha_text = ''.join(random.choice(characters) for _ in range(length))

        # Создание изображения
        image = Image.new('RGB', (120, 40), color=(255, 255, 255))
        draw = ImageDraw.Draw(image)

        # 3. Добавляем шум (точки)
        for _ in range(100):
            x = random.randint(0, 120)
            y = random.randint(0, 40)
            draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))

        # 4. Рисуем текст
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((10, 10), captcha_text, fill=(0, 0, 0), font=font)

        # 5. Сохраняем в bytes
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        return captcha_text, buffer

