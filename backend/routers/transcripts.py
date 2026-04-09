"""
Transcript & Project CRUD routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.db_models import Project, Transcript, ActionItem, SentimentSegment
from backend.schemas.pydantic_schemas import (
    ProjectCreate, ProjectResponse,
    TranscriptListItem, TranscriptDetail, TranscriptUploadResponse,
    DashboardStats,
)
from backend.services.parser_service import parse_txt, parse_vtt

router = APIRouter()


# ── Projects ─────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    result = []
    for p in projects:
        result.append(ProjectResponse(
            id=p.id,
            name=p.name,
            created_at=p.created_at,
            transcript_count=len(p.transcripts),
        ))
    return result


@router.post("/projects", response_model=ProjectResponse)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(name=payload.name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at,
        transcript_count=0,
    )


@router.delete("/projects/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


# ── Dashboard stats ──────────────────────────────────

@router.get("/projects/{project_id}/stats", response_model=DashboardStats)
def project_stats(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    transcripts = project.transcripts
    all_items = []
    sentiment_scores = []

    for t in transcripts:
        all_items.extend(t.action_items)
        for s in t.sentiment_segments:
            sentiment_scores.append(
                1.0 if s.sentiment.value == "positive"
                else 0.0 if s.sentiment.value == "neutral"
                else -1.0
            )

    decisions = [i for i in all_items if i.type.value == "decision"]
    actions = [i for i in all_items if i.type.value == "action_item"]
    avg_sent = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

    recent = sorted(transcripts, key=lambda t: t.uploaded_at, reverse=True)[:5]

    return DashboardStats(
        total_transcripts=len(transcripts),
        total_action_items=len(actions),
        total_decisions=len(decisions),
        avg_sentiment_score=round(avg_sent, 2),
        recent_meetings=[TranscriptListItem.model_validate(t) for t in recent],
    )


# ── Transcripts ──────────────────────────────────────

@router.post("/transcripts/upload", response_model=TranscriptUploadResponse)
async def upload_transcript(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    content = (await file.read()).decode("utf-8", errors="replace")
    fname = file.filename or "untitled.txt"

    # Parse
    if fname.lower().endswith(".vtt"):
        parsed = parse_vtt(content)
    else:
        parsed = parse_txt(content)

    # Resolve or create project
    if project_id:
        proj = db.query(Project).filter(Project.id == project_id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found")
    elif project_name:
        proj = db.query(Project).filter(Project.name == project_name).first()
        if not proj:
            proj = Project(name=project_name)
            db.add(proj)
            db.flush()
    else:
        name = fname.rsplit(".", 1)[0].replace("_", " ").title()
        proj = Project(name=name)
        db.add(proj)
        db.flush()

    transcript = Transcript(
        project_id=proj.id,
        file_name=fname,
        raw_text=parsed["raw_text"],
        meeting_date=parsed.get("meeting_date"),
        speaker_count=parsed.get("speaker_count", 0),
        word_count=parsed.get("word_count", 0),
    )
    db.add(transcript)
    db.commit()
    db.refresh(transcript)

    return TranscriptUploadResponse(
        id=transcript.id,
        file_name=transcript.file_name,
        speaker_count=transcript.speaker_count,
        word_count=transcript.word_count,
        meeting_date=transcript.meeting_date,
        message=f"Uploaded to project '{proj.name}'",
    )


@router.get("/transcripts/{project_id}", response_model=List[TranscriptListItem])
def list_transcripts(project_id: str, db: Session = Depends(get_db)):
    items = (
        db.query(Transcript)
        .filter(Transcript.project_id == project_id)
        .order_by(Transcript.uploaded_at.desc())
        .all()
    )
    return [TranscriptListItem.model_validate(t) for t in items]


@router.get("/transcripts/{transcript_id}/detail", response_model=TranscriptDetail)
def get_transcript_detail(transcript_id: str, db: Session = Depends(get_db)):
    t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    return TranscriptDetail.model_validate(t)


@router.delete("/transcripts/{transcript_id}")
def delete_transcript(transcript_id: str, db: Session = Depends(get_db)):
    t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")
    db.delete(t)
    db.commit()
    return {"message": "Transcript deleted"}
