"""才能精進路由 - 優化努力方式"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import AbilityProfile, LearningRecord
from services.ai_service import get_ai_response
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.post("/{student_id}/strength-analysis")
async def strength_analysis(student_id: int, db: AsyncSession = Depends(get_db)):
    """長板優勢識別"""
    student = await get_student_full(db, student_id)
    if not student:
        return {"error": "學生不存在"}

    ctx = student_to_context(student)

    message = (
        f"基於我的能力畫像和興趣圖譜，請分析：\n"
        f"1. 我最突出的「長板」是什麼？（優勢領域）\n"
        f"2. 我的獨特性在哪裡？\n"
        f"3. 如何把我的優勢發揮到極致？\n"
        f"4. 我的興趣和優勢有什麼交叉點？那就是最有潛力的方向\n\n"
        f"記住：沒有突出的長板就是危險。幫我找到並發展我的核心優勢。"
    )

    stream = await get_ai_response("talent_growth", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/design-challenge")
async def design_challenge(
    student_id: int,
    scenario: str,
    current_topic: str = "",
    db: AsyncSession = Depends(get_db),
):
    """設計「必要的難度」挑戰"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    topic_hint = f"，當前學習主題是「{current_topic}」" if current_topic else ""

    message = (
        f"我想在{scenario}方面進行挑戰練習{topic_hint}。\n\n"
        f"請根據我的當前能力水平，設計一個「必要的難度」挑戰：\n"
        f"1. 這個挑戰要略高於我的舒適區，但不至於讓我挫敗\n"
        f"2. 完成這個挑戰能帶來明顯的成長\n"
        f"3. 挑戰要具體可執行，不是空泛的目標\n"
        f"4. 嘗試將挑戰與我的興趣結合，用興趣驅動而非意志力鞭策\n\n"
        f"記住：挑戰是設計出來的，好的挑戰讓人欲罷不能。"
    )

    stream = await get_ai_response("talent_growth", scenario, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{student_id}/growth-trajectory")
async def growth_trajectory(student_id: int, db: AsyncSession = Depends(get_db)):
    """進度可視化 - 成長軌跡數據"""
    result = await db.execute(
        select(LearningRecord)
        .where(LearningRecord.student_id == student_id)
        .order_by(LearningRecord.created_at)
    )
    records = result.scalars().all()

    trajectory = []
    for r in records:
        trajectory.append({
            "date": r.created_at.isoformat() if r.created_at else None,
            "module": r.module.value if r.module else None,
            "scenario": r.scenario.value if r.scenario else None,
            "score": r.score,
            "duration": r.duration_minutes,
        })

    return {"trajectory": trajectory, "total_records": len(trajectory)}
