from dataclasses import dataclass
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.comment import Comments
from src.schemas.comment import CommentCreateSchema


@dataclass
class CommentRepository:
    session: AsyncSession

    async def create_comment(self, comment: CommentCreateSchema) -> Comments:
        db_comment = Comments(
            user_name=comment.user_name,
            email=comment.email,
            home_page=str(comment.home_page) if comment.home_page else None,
            text=comment.text,
            parent_id=comment.parent_id or None,
            file_path=getattr(comment, "file_path", None),
            file_type=getattr(comment, "file_type", None),
            image_w=getattr(comment, "image_w", None),
            image_h=getattr(comment, "image_h", None),
        )
        self.session.add(db_comment)
        await self.session.commit()
        await self.session.refresh(db_comment)
        return db_comment

    async def get_all_comments_with_replies(self) -> list[Comments]:
        """Получить все комментарии с вложенной структурой"""
        # Получаем ВСЕ комментарии
        result = await self.session.execute(
            select(Comments).order_by(Comments.created_at.desc())
        )
        all_comments = list(result.scalars().all())

        # Строим дерево
        comments_dict = {comment.id: comment for comment in all_comments}

        for comment in all_comments:
            comment.replies = []

        root_comments = []
        for comment in all_comments:
            if comment.parent_id is None:
                root_comments.append(comment)
            else:
                parent = comments_dict.get(comment.parent_id)
                if parent:
                    parent.replies.append(comment)

        return root_comments

    # async def get_comment_by_id(self, comment_id: int) -> Optional[Comments]:
    #     result = await self.session.execute(
    #         select(Comments).where(Comments.id == comment_id)
    #     )
    #     return result.scalars().first()
    #
    # async def get_comments(
    #     self,
    #     skip: int = 0,
    #     limit: int = 25,
    #     sort_by: str = "created_at",
    #     order: str = "desc",  # order как сортировать
    # ) -> list[Comments]:
    #     """
    #     Получение корневых комментариев (parent_id is None)
    #     с пагинацией и сортировкой.
    #     """
    #     query = select(Comments).where(Comments.parent_id == None)
    #     column = getattr(Comments, sort_by)  # динамический выбор поля
    #
    #     # desc() → по убыванию (от большего к меньшему, LIFO по дате)
    #     # asc() → по возрастанию (от меньшего к большему, FIFO по дате)
    #
    #     query = query.order_by(column.desc() if order == "desc" else column.asc())
    #     result = await self.session.execute(query.offset(skip).limit(limit))
    #     return list(result.scalars().all())
    #
    # async def update_comment(self, db_comment: Comments, **kwargs) -> Comments:
    #     for key, value in kwargs.items():
    #         if hasattr(db_comment, key):
    #             setattr(db_comment, key, value)
    #     await self.session.commit()
    #     await self.session.refresh(db_comment)
    #     return db_comment
    #
    # async def delete_comment(self, db_comment: Comments) -> int:
    #     await self.session.delete(db_comment)
    #     await self.session.commit()
    #     return db_comment.id
    #
    # # Получение всех ответов на комментарий(asc чтобы ответы шли сверху вниз)
    # async def get_replies(self, parent_id: int) -> Sequence[Comments]:
    #     result = await self.session.execute(
    #         select(Comments)
    #         .where(Comments.parent_id == parent_id)
    #         .order_by(Comments.created_at.asc())  # ответы сверху вниз
    #     )
    #     replies = result.scalars().all()
    #
    #     # рекурсивно получить ответы на ответы
    #     for reply in replies:
    #         reply.replies = await self.get_replies(reply.id)
    #     return replies
