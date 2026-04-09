"""
Sentiment analysis routes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Transcript, SentimentSegment, SentimentType
from backend.schemas.pydantic_schemas import SentimentSegmentResponse
from backend.services import gemini_service
from backend.services.parser_service import parse_txt

router = APIRouter()


@router.post("/sentiment/{transcript_id}", response_model=List[SentimentSegmentResponse])
def run_sentiment(transcript_id: str, db: Session = Depends(get_db)):
    t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Clear previous sentiment data
    db.query(SentimentSegment).filter(SentimentSegment.transcript_id == transcript_id).delete()
    db.flush()

    # Re-parse to get segments
    parsed = parse_txt(t.raw_text)
    segments = parsed.get("segments", [])

    if not segments:
        segments = [{"speaker": "Unknown", "text": t.raw_text}]

    results = gemini_service.analyze_sentiment(segments)

    db_segments = []
    for i, r in enumerate(results):
        seg = SentimentSegment(
            transcript_id=transcript_id,
            speaker=r.get("speaker", segments[i].get("speaker", "Unknown") if i < len(segments) else "Unknown"),
            segment_text=segments[i]["text"] if i < len(segments) else "",
            sentiment=SentimentType(r["sentiment"]),
            tone=r.get("tone", ""),
            segment_index=r.get("segment_index", i + 1),
        )
        db.add(seg)
        db_segments.append(seg)

    db.commit()
    for seg in db_segments:
        db.refresh(seg)

    return [SentimentSegmentResponse.model_validate(s) for s in db_segments]


@router.get("/sentiment/{transcript_id}", response_model=List[SentimentSegmentResponse])
def get_sentiment(transcript_id: str, db: Session = Depends(get_db)):
    segments = (
        db.query(SentimentSegment)
        .filter(SentimentSegment.transcript_id == transcript_id)
        .order_by(SentimentSegment.segment_index)
        .all()
    )
    return [SentimentSegmentResponse.model_validate(s) for s in segments]
