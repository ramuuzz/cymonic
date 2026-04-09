from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from enum import Enum


class ActionItemTypeEnum(str, Enum):
    decision = "decision"
    action_item = "action_item"


class SentimentEnum(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"


class ChatRoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"


# ── Project ──────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    transcript_count: int = 0

    class Config:
        from_attributes = True


# ── Transcript ───────────────────────────────────────
class TranscriptListItem(BaseModel):
    id: str
    file_name: str
    meeting_date: Optional[date] = None
    speaker_count: int
    word_count: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class TranscriptDetail(TranscriptListItem):
    project_id: str
    raw_text: str


class TranscriptUploadResponse(BaseModel):
    id: str
    file_name: str
    speaker_count: int
    word_count: int
    meeting_date: Optional[date] = None
    message: str


# ── Action Items ─────────────────────────────────────
class ActionItemResponse(BaseModel):
    id: str
    transcript_id: str
    type: ActionItemTypeEnum
    owner: Optional[str] = None
    description: str
    due_date: Optional[str] = None

    class Config:
        from_attributes = True


class ActionItemUpdate(BaseModel):
    type: Optional[ActionItemTypeEnum] = None
    owner: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None


class ExtractionResult(BaseModel):
    decisions: List[ActionItemResponse]
    action_items: List[ActionItemResponse]
    total_count: int


# ── Sentiment ────────────────────────────────────────
class SentimentSegmentResponse(BaseModel):
    id: str
    transcript_id: str
    speaker: Optional[str] = None
    segment_text: str
    sentiment: SentimentEnum
    tone: Optional[str] = None
    segment_index: int

    class Config:
        from_attributes = True


# ── Chat ─────────────────────────────────────────────
class ChatMessageCreate(BaseModel):
    message: str


class ChatResponse(BaseModel):
    role: ChatRoleEnum
    message: str
    cited_transcript_id: Optional[str] = None
    cited_meeting_name: Optional[str] = None


class ChatHistoryItem(BaseModel):
    id: str
    role: ChatRoleEnum
    message: str
    cited_transcript_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Dashboard ────────────────────────────────────────
class DashboardStats(BaseModel):
    total_transcripts: int
    total_action_items: int
    total_decisions: int
    avg_sentiment_score: float
    recent_meetings: List[TranscriptListItem]
