from typing import Annotated

from fastapi import APIRouter, Depends

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder

from src.core.websocket import manager
from src.dependecy import get_comment_service
from src.schemas.comment import CommentResponseSchema
from src.services.comment import CommentService

router = APIRouter(prefix='/ws', tags=["web_socket"])


@router.websocket("/comments")
async def websocket_endpoint(
    ws: WebSocket,
    service: Annotated[CommentService, Depends(get_comment_service)]
):
    comments = await service.get_all_comments()
    comments_data = [CommentResponseSchema.model_validate(c) for c in comments]
    comments_json = jsonable_encoder(comments_data)

    # Подключаем через manager
    await manager.connect(ws, comments_json)

    try:
        while True:
            msg = await ws.receive_text()
            print("WS: получено сообщение от клиента:", msg)
            # обработка ping или других сообщений
    except WebSocketDisconnect:
        manager.disconnect(ws)
        print("WS: клиент отключился")