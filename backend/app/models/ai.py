"""
StockVision AI - AI Conversation Model
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AIConversation(Base):
    """
    Stores AI assistant chat history for context and audit purposes.

    Each row is one message in a conversation. Messages are grouped
    by session_id.

    role values:
        user      - Message from the employee/manager
        assistant - Response from the AI assistant
        system    - System prompt or context
    """

    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tool_calls: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (
            f"<AIConversation(session='{self.session_id}', "
            f"role='{self.role}', content='{preview}')>"
        )
