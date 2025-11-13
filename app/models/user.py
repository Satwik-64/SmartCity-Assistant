"""ORM models for the Smart City Assistant platform."""
from __future__ import annotations

from datetime import datetime
import enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class UserType(enum.Enum):
    USER = "user"
    AUTHORITY = "authority"


class FeedbackStatus(enum.Enum):
    REPORTED = "reported"
    IN_PROCESS = "in_process"
    SOLVED = "solved"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("phone_number", name="uq_users_phone_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    address = Column(String(500), nullable=True)
    department = Column(String(255), nullable=True)
    position = Column(String(255), nullable=True)
    feedback_route = Column(String(255), nullable=True)
    user_type = Column(Enum(UserType), default=UserType.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_login = Column(DateTime(timezone=True), nullable=True)

    feedbacks = relationship(
        "Feedback",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Feedback.user_id",
    )
    assigned_feedbacks = relationship(
        "Feedback",
        back_populates="assigned_authority",
        foreign_keys="Feedback.authority_id",
    )
    chat_messages = relationship(
        "ChatMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    announcements = relationship(
        "Announcement",
        back_populates="author",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r} type={self.user_type.value}>"

    # No dedicated admin flag; authorities and users share the same workflow.


class Feedback(Base):
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    authority_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    category = Column(String(120), nullable=False)
    message = Column(Text, nullable=False)
    authority_type = Column(String(120), nullable=True)
    priority = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    status = Column(Enum(FeedbackStatus), default=FeedbackStatus.REPORTED, nullable=False)
    authority_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user = relationship("User", foreign_keys=[user_id], back_populates="feedbacks")
    assigned_authority = relationship(
        "User", foreign_keys=[authority_id], back_populates="assigned_feedbacks"
    )

    def __repr__(self) -> str:
        return f"<Feedback id={self.id} status={self.status.value}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="chat_messages")

    def __repr__(self) -> str:
        created = self.created_at.isoformat() if isinstance(self.created_at, datetime) else "--"
        return f"<ChatMessage user_id={self.user_id} sender={self.sender!r} created_at={created}>"


class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    audience = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    author = relationship("User", back_populates="announcements")

    def __repr__(self) -> str:
        return f"<Announcement id={self.id} title={self.title!r}>"
