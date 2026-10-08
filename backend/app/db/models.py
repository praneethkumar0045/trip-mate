from datetime import datetime

from sqlalchemy import (
    String,
    Text,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")

    messages = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"), nullable=False
    )

    role: Mapped[str] = mapped_column(String(50), nullable=False)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")
