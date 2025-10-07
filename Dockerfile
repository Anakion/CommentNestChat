FROM python:3.13-slim

# Системные библиотеки для Pillow и шрифты
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    libfreetype6 \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Сначала ставим uv
RUN pip install --no-cache-dir uv

# Устанавливаем зависимости проекта через uv
RUN uv pip install --system --no-cache .

# Запуск приложения
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
