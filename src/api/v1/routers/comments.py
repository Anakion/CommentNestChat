import json
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder

from src.core.websocket import manager
from src.dependecy import get_comment_service
from src.schemas.comment import CommentResponseSchema, CommentCreateSchema
from src.services.comment import CommentService

router = APIRouter(prefix="/comments", tags=["comments"])


# @router.post("/", response_model=CommentResponseSchema)
# async def create_comment(
#     payload: CommentCreateSchema,
#     service: Annotated[CommentService, Depends(get_comment_service)],
# ):
#     new_comment = await service.create_comment(payload)
#
#     # Можно разослать всем только новый коммент
#
#     await manager.broadcast_new_comment({
#         "type": "new_comment",
#         "data": CommentResponseSchema.model_validate(new_comment)
#     })
#     print("Broadcasted new_comment:", new_comment.id)
#
#     return new_comment

@router.post("/", response_model=CommentResponseSchema)
async def create_comment(
    payload: CommentCreateSchema,
    service: Annotated[CommentService, Depends(get_comment_service)],
):
    new_comment = await service.create_comment(payload)

    # Преобразуем модель в dict для фронта
    comment_dict = jsonable_encoder(CommentResponseSchema.model_validate(new_comment))
    print("Отправляем новый комментарий:", comment_dict)
    await manager.broadcast_new_comment({
        "type": "new_comment",
        "data": comment_dict
    })
    print("Broadcasted new_comment:", new_comment.id)

    return new_comment


@router.get("/", response_model=List[CommentResponseSchema])
async def get_all_comments(
    service: Annotated[CommentService, Depends(get_comment_service)],
):
    return await service.get_all_comments()