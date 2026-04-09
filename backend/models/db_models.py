import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, DateTime, Date, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from backend.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class ActionItemType(str, enum.Enum):
    decision = "decision"
    action_item = "action_item"


class SentimentType(str, enum.Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    transcripts = relationship("Transcript", back_populates="project", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="project", cascade="all, delete-orphan")


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    raw_text = Column(Text, nullable=False)
    meeting_date = Column(Date, nullable=True)
    speaker_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="transcripts")
    action_items = relationship("ActionItem", back_populates="transcript", cascade="all, delete-orphan")
    sentiment_segments = relationship("SentimentSegment", back_populates="transcript", cascade="all, delete-orphan")


class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    type = Column(SAEnum(ActionItemType, name="action_item_type", create_constraint=True), nullable=False)
    owner = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    due_date = Column(String(100), nullable=True)

    transcript = relationship("Transcript", back_populates="action_items")


class SentimentSegment(Base):
    __tablename__ = "sentiment_segments"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    transcript_id = Column(String(36), ForeignKey("transcripts.id", ondelete="CASCADE"), nullable=False)
    speaker = Column(String(255), nullable=True)
    segment_text = Column(Text, nullable=False)
    sentiment = Column(SAEnum(SentimentType, name="sentiment_type", create_constraint=True), nullable=False)
    tone = Column(String(100), nullable=True)
    segment_index = Column(Integer, default=0)

    transcript = relationship("Transcript", back_populates="sentiment_segments")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    role = Column(SAEnum(ChatRole, name="chat_role", create_constraint=True), nullable=False)
    message = Column(Text, nullable=False)
    cited_transcript_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="chat_history")
