from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.core.config import settings

engine = create_async_engine(settings.database_url, echo=settings.ECHO)


class Base(DeclarativeBase): ...
