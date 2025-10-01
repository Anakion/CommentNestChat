import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from src.api.v1.routers import comments
from src.api.v1.routers import websocket
from src.core.config import settings
from src.core.websocket import manager
from src.repositories.comment_repo import CommentRepository
from src.services.comment import CommentService


from src.dependecy import get_db  # твой генератор сессии
from src.repositories.comment_repo import CommentRepository
from src.services.comment import CommentService


# Получаем абсолютный путь к корню проекта
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(PROJECT_ROOT)
STATIC_DIR = os.path.join(BASE_DIR, "static")

async def check_db_changes(service: CommentService):
    last_state = None
    while True:
        print("💡 check_db_changes проверка БД...")  # <-- добавили лог
        await asyncio.sleep(2)  # интервал проверки
        current_state = await service.get_all_comments()  # ⚡ async если это БД
        current_json = jsonable_encoder(current_state)
        if current_json != last_state:
            print("💡 Изменения найдены, рассылаем клиентам")
            await manager.broadcast_comments(current_json)
            last_state = current_json


@asynccontextmanager
async def lifespan(app: FastAPI):
    async for session in get_db():  # ⚡ берем сессию из генератора
        repo = CommentRepository(session=session)
        service = CommentService(repository=repo, settings=settings)

        task = asyncio.create_task(check_db_changes(service))
        yield  # приложение запускается здесь

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        break  # используем только одну сессию

app = FastAPI(lifespan=lifespan)

# 1. СНАЧАЛА регистрируем API роуты и WebSocket
app.include_router(comments.router)
app.include_router(websocket.router)

# 2. Главная страница
@app.get("/")
async def root():
    with open(os.path.join(STATIC_DIR, "home.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

print("=== THIS IS COMMENTNESTCHAT ===")

# 3. ПОСЛЕДНИМ монтируем статику (НЕ на корневой путь!)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)