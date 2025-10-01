from datetime import datetime

from sqlalchemy import (Integer, String,
                        Text, DateTime,
                        ForeignKey, Index)
from sqlalchemy.orm import mapped_column, Mapped, relationship

from src.db.base import Base


class Comments(Base):
    __tablename__ = "comments"
    __table_args__ = (
        Index("idx_created_at", "created_at"),
        Index("idx_user_email", "user_name", "email"),
        Index("idx_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_name: Mapped[str] = mapped_column(String(60), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    home_page: Mapped[str] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    file_path: Mapped[str] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)
    image_w: Mapped[int] = mapped_column(Integer, nullable=True)
    image_h: Mapped[int] = mapped_column(Integer, nullable=True)

    # Родитель
    parent: Mapped["Comments"] = relationship(
        "Comments",
        remote_side=[id],          # важный момент!
        back_populates="replies"
    )

    # Дети
    replies: Mapped[list["Comments"]] = relationship(
        "Comments",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="noload"
    )