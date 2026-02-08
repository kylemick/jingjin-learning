"""時間羅盤路由 - 時間之尺"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from database.models import TimeEntry
from schemas import TimeEntryCreate, TimeEntryOut, AIRequest
from services.ai_service import get_ai_response
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.get("/{student_id}/entries", response_model=list[TimeEntryOut])
async def list_time_entries(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TimeEntry).where(TimeEntry.student_id == student_id).order_by(TimeEntry.date.desc())
    )
    return result.scalars().all()


@router.post("/{student_id}/entries", response_model=TimeEntryOut)
async def add_time_entry(student_id: int, data: TimeEntryCreate, db: AsyncSession = Depends(get_db)):
    entry = TimeEntry(student_id=student_id, **data.model_dump())
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


@router.get("/{student_id}/stats")
async def time_stats(student_id: int, db: AsyncSession = Depends(get_db)):
    """時間使用統計"""
    result = await db.execute(
        select(
            TimeEntry.half_life,
            func.sum(TimeEntry.duration_minutes).label("total_minutes"),
            func.count(TimeEntry.id).label("count"),
        )
        .where(TimeEntry.student_id == student_id)
        .group_by(TimeEntry.half_life)
    )
    rows = result.all()
    stats = {row.half_life: {"total_minutes": row.total_minutes, "count": row.count} for row in rows}
    return stats


@router.post("/{student_id}/ai-analyze")
async def ai_analyze_time(student_id: int, db: AsyncSession = Depends(get_db)):
    """AI 分析時間使用品質"""
    student = await get_student_full(db, student_id)
    if not student:
        return {"error": "學生不存在"}

    # 獲取最近的時間記錄
    result = await db.execute(
        select(TimeEntry)
        .where(TimeEntry.student_id == student_id)
        .order_by(TimeEntry.date.desc())
        .limit(20)
    )
    entries = result.scalars().all()

    entries_text = "\n".join([
        f"- {e.activity}（{e.duration_minutes}分鐘, 半衰期:{e.half_life}, 收益值:{e.benefit_value}）"
        for e in entries
    ])

    message = f"請分析以下時間使用記錄，指出哪些是長半衰期活動、哪些是短半衰期活動，給出改進建議：\n{entries_text}"

    ctx = student_to_context(student)
    stream = await get_ai_response("time_compass", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
