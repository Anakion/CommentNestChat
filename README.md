# CommentNestChat

CommentNestChat - это современная система комментирования с веб-интерфейсом, реализованная на FastAPI с использованием WebSockets для обновления комментариев в реальном времени.

## 🚀 Основные возможности

- 📝 Создание и просмотр комментариев
- 🔄 Обновление комментариев в реальном времени через WebSockets
- 🔒 Защита от спама с помощью капчи
- 🗂️ Иерархическая структура комментариев
- 🎨 Адаптивный веб-интерфейс

## 🛠️ Технологический стек

- **Бэкенд**: FastAPI (Python 3.10+)
- **База данных**: PostgreSQL
- **Кэширование**: Redis
- **Асинхронность**: asyncio
- **Фронтенд**: HTML, JavaScript (нативный)
- **Развертывание**: Docker, Docker Compose

## 🚀 Быстрый старт

### Требования

- Docker и Docker Compose
- Python 3.10+

### Установка и запуск

1. Клонируйте репозиторий:
   ```bash
   git clone <your-repository-url>
   cd CommentNestChat
   ```

2. Настройте переменные окружения в файле `.dev.env`:
   ```
   DATABASE_URL=postgresql://user:password@postgres:5432/dbname
   REDIS_URL=redis://redis:6379
   SECRET_KEY=your-secret-key
   ```

3. Запустите приложение с помощью Docker Compose:
   ```bash
   docker-compose up --build -d
   ```

4. Примените миграции базы данных:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

5. Приложение будет доступно по адресу: [http://localhost:8000](http://localhost:8000)

## 🏗️ Структура проекта

```
CommentNestChat/
├── src/                    # Исходный код приложения
│   ├── api/                # API эндпоинты
│   ├── core/               # Основные настройки и конфигурации
│   ├── db/                 # Настройки базы данных
│   ├── models/             # Модели данных
│   ├── repositories/       # Репозитории для работы с БД
│   ├── schemas/            # Pydantic схемы
│   ├── services/           # Бизнес-логика
│   └── use_cases/          # Сценарии использования
├── static/                 # Статические файлы (CSS, JS, изображения)
├── migrations/             # Миграции базы данных
├── .dev.env                # Переменные окружения
├── docker-compose.yml      # Конфигурация Docker Compose
└── Dockerfile              # Конфигурация Docker
```

## 🌐 API Endpoints

- `GET /` - Основная страница с комментариями
- `POST /api/v1/comments/` - Создание нового комментария
- `GET /api/v1/comments/` - Получение списка комментариев
- `GET /api/v1/captcha/` - Получение капчи
- `POST /api/v1/captcha/verify/` - Проверка капчи

## 🔌 WebSocket

Приложение поддерживает обновление комментариев в реальном времени через WebSocket по адресу `/ws/comments`.

