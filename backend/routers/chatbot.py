"""
Chatbot routes — Q&A over transcripts.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Project, Transcript, ChatHistory, ChatRole
from backend.schemas.pydantic_schemas import (
    ChatMessageCreate, ChatResponse, ChatHistoryItem,
)
from backend.services import gemini_service

router = APIRouter()


@router.post("/chat/{project_id}", response_model=ChatResponse)
def chat(project_id: str, payload: ChatMessageCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Gather all transcripts for this project
    transcripts = db.query(Transcript).filter(Transcript.project_id == project_id).all()
    if not transcripts:
        return ChatResponse(
            role="assistant",
            message="No transcripts found in this project. Please upload meeting transcripts first.",
        )

    transcript_texts = [
        {"name": t.file_name, "text": t.raw_text, "id": str(t.id)}
        for t in transcripts
    ]

    # Build chat history from DB
    history_rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.project_id == project_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    chat_history = [{"role": h.role.value, "message": h.message} for h in history_rows]

    # Save user message
    user_msg = ChatHistory(
        project_id=project_id,
        role=ChatRole.user,
        message=payload.message,
    )
    db.add(user_msg)
    db.flush()

    # Get AI response
    result = gemini_service.chat_with_context(payload.message, transcript_texts, chat_history)

    # Find cited transcript ID
    cited_id = None
    cited_name = result.get("cited_meeting")
    if cited_name:
        for t in transcripts:
            if t.file_name.lower() == cited_name.lower():
                cited_id = t.id
                break

    # Save assistant message
    asst_msg = ChatHistory(
        project_id=project_id,
        role=ChatRole.assistant,
        message=result["answer"],
        cited_transcript_id=cited_id,
    )
    db.add(asst_msg)
    db.commit()

    return ChatResponse(
        role="assistant",
        message=result["answer"],
        cited_transcript_id=cited_id,
        cited_meeting_name=cited_name,
    )


@router.get("/chat/{project_id}/history", response_model=List[ChatHistoryItem])
def get_chat_history(project_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.project_id == project_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return [ChatHistoryItem.model_validate(r) for r in rows]


@router.delete("/chat/{project_id}/history")
def clear_chat_history(project_id: str, db: Session = Depends(get_db)):
    db.query(ChatHistory).filter(ChatHistory.project_id == project_id).delete()
    db.commit()
    return {"message": "Chat history cleared"}
