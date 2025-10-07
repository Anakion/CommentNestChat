import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.encoders import jsonable_encoder
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles

from src.api.v1.routers import comments
from src.api.v1.routers import websocket
from src.api.v1.routers import captcha
from src.core.config import settings
from src.core.websocket import manager

from starlette.middleware.sessions import SessionMiddleware
import secrets

from src.repositories.comment_repo import CommentRepository
from src.services.comment import CommentService

from src.dependecy import get_db
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
    async for session in get_db():
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

app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
    session_cookie="sessionid",
    max_age=3600,  # 1 час
)

app.include_router(comments.router)
app.include_router(websocket.router)
app.include_router(captcha.router)


@app.get("/")
async def root():
    with open(os.path.join(STATIC_DIR, "home.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True)
