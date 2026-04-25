"""
Extraction routes — trigger AI extraction and manage action items.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from backend.database import get_db
from backend.models.db_models import Transcript, ActionItem, ActionItemType
from backend.schemas.pydantic_schemas import (
    ActionItemResponse, ActionItemUpdate, ExtractionResult,
)
from backend.services import gemini_service, export_service

router = APIRouter()


@router.post("/extraction/{transcript_id}", response_model=ExtractionResult)
def run_extraction(transcript_id: str, db: Session = Depends(get_db)):
    t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")

    # Clear previous extractions
    db.query(ActionItem).filter(ActionItem.transcript_id == transcript_id).delete()
    db.flush()

    result = gemini_service.extract_action_items(t.raw_text)

    all_items = []
    for d in result.get("decisions", []):
        item = ActionItem(
            transcript_id=transcript_id,
            type=ActionItemType.decision,
            owner=d.get("owner"),
            description=d.get("description", "No description provided"),
            due_date=d.get("due_date"),
        )
        db.add(item)
        all_items.append(item)

    for a in result.get("action_items", []):
        item = ActionItem(
            transcript_id=transcript_id,
            type=ActionItemType.action_item,
            owner=a.get("owner", "Unassigned"),
            description=a.get("description", "No description provided"),
            due_date=a.get("due_date"),
        )
        db.add(item)
        all_items.append(item)

    db.commit()
    for item in all_items:
        db.refresh(item)

    decisions = [ActionItemResponse.model_validate(i) for i in all_items if i.type == ActionItemType.decision]
    actions = [ActionItemResponse.model_validate(i) for i in all_items if i.type == ActionItemType.action_item]

    return ExtractionResult(
        decisions=decisions,
        action_items=actions,
        total_count=len(all_items),
    )


@router.get("/extraction/{transcript_id}/items", response_model=List[ActionItemResponse])
def get_extraction_items(transcript_id: str, db: Session = Depends(get_db)):
    items = (
        db.query(ActionItem)
        .filter(ActionItem.transcript_id == transcript_id)
        .all()
    )
    return [ActionItemResponse.model_validate(i) for i in items]


@router.put("/extraction/item/{item_id}", response_model=ActionItemResponse)
def update_action_item(item_id: str, payload: ActionItemUpdate, db: Session = Depends(get_db)):
    item = db.query(ActionItem).filter(ActionItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")

    if payload.type is not None:
        item.type = ActionItemType(payload.type.value)
    if payload.owner is not None:
        item.owner = payload.owner
    if payload.description is not None:
        item.description = payload.description
    if payload.due_date is not None:
        item.due_date = payload.due_date

    db.commit()
    db.refresh(item)
    return ActionItemResponse.model_validate(item)


@router.get("/extraction/{transcript_id}/export")
def export_items(
    transcript_id: str,
    format: str = Query("csv", regex="^(csv|pdf)$"),
    db: Session = Depends(get_db),
):
    t = db.query(Transcript).filter(Transcript.id == transcript_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transcript not found")

    items = db.query(ActionItem).filter(ActionItem.transcript_id == transcript_id).all()
    data = [
        {
            "type": i.type.value,
            "owner": i.owner or "",
            "description": i.description,
            "due_date": i.due_date or "",
        }
        for i in items
    ]

    if format == "csv":
        content = export_service.export_csv(data)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={t.file_name}_items.csv"},
        )
    else:
        content = export_service.export_pdf(data, meeting_name=t.file_name)
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={t.file_name}_items.pdf"},
        )
