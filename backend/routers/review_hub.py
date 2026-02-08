"""成長復盤路由 - 創造獨特成功"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database.connection import get_db
from database.models import LearningRecord, FeedbackSummary, AbilityProfile
from schemas import ReflectionCreate, LearningRecordOut, FeedbackSummaryOut
from services.ai_service import get_ai_response, get_ai_response_full
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.get("/{student_id}/records", response_model=list[LearningRecordOut])
async def list_records(
    student_id: int,
    module: str = None,
    scenario: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    query = select(LearningRecord).where(LearningRecord.student_id == student_id)
    if module:
        query = query.where(LearningRecord.module == module)
    if scenario:
        query = query.where(LearningRecord.scenario == scenario)
    query = query.order_by(LearningRecord.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{student_id}/reflect")
async def add_reflection(student_id: int, data: ReflectionCreate, db: AsyncSession = Depends(get_db)):
    """三行而後思 - 提交反思"""
    result = await db.execute(
        select(LearningRecord).where(
            LearningRecord.id == data.record_id,
            LearningRecord.student_id == student_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="學習記錄不存在")

    record.reflection = data.reflection
    await db.flush()
    return {"ok": True, "record_id": record.id}


@router.post("/{student_id}/deep-feedback")
async def deep_feedback(
    student_id: int,
    scenario: str,
    content: str,
    db: AsyncSession = Depends(get_db),
):
    """AI 深度反饋"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"以下是我的練習/作品內容：\n{content}\n\n"
        f"請給出深度反饋，包括：\n"
        f"1. 具體的優點（哪裡做得好，為什麼好）\n"
        f"2. 具體的改進建議（哪裡可以更好，怎麼改）\n"
        f"3. 我展現出的獨特特質（與眾不同的地方）\n"
        f"4. 下一步精進方向\n"
        f"5. 結合我的歷史表現，指出進步的地方\n\n"
        f"記住：每個學生都是獨特的，幫我發現我的成長軌跡。"
    )

    stream = await get_ai_response("review_hub", scenario, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/update-profile-from-feedback")
async def update_profile_from_feedback(
    student_id: int,
    scenario: str,
    db: AsyncSession = Depends(get_db),
):
    """根據學習記錄更新個人檔案（精進閉環的關鍵環節）"""
    student = await get_student_full(db, student_id)
    if not student:
        return {"error": "學生不存在"}

    # 獲取最近的學習記錄
    result = await db.execute(
        select(LearningRecord)
        .where(LearningRecord.student_id == student_id)
        .where(LearningRecord.scenario == scenario)
        .order_by(LearningRecord.created_at.desc())
        .limit(10)
    )
    records = result.scalars().all()

    if not records:
        return {"message": "暫無學習記錄"}

    ctx = student_to_context(student)
    records_text = "\n".join([
        f"- 內容:{r.content[:200] if r.content else '無'} | 反饋:{r.ai_feedback[:200] if r.ai_feedback else '無'} | 得分:{r.score}"
        for r in records
    ])

    message = (
        f"以下是學生最近在{scenario}場景的學習記錄：\n{records_text}\n\n"
        f"請分析並以 JSON 格式返回以下內容：\n"
        f'{{"strengths": "優勢摘要", "weaknesses": "短板摘要", "progress_trend": "進步趨勢描述", '
        f'"ai_suggestions": "具體的改進建議"}}\n'
        f"只返回 JSON，不要其他內容。"
    )

    response = await get_ai_response_full("review_hub", scenario, ctx, message)

    # 更新反饋摘要
    fb_result = await db.execute(
        select(FeedbackSummary).where(
            FeedbackSummary.student_id == student_id,
            FeedbackSummary.scenario == scenario,
        )
    )
    fb = fb_result.scalar_one_or_none()
    if not fb:
        fb = FeedbackSummary(student_id=student_id, scenario=scenario)
        db.add(fb)

    # 嘗試解析 AI 回覆
    try:
        data = json.loads(response)
        fb.strengths = data.get("strengths", "")
        fb.weaknesses = data.get("weaknesses", "")
        fb.progress_trend = data.get("progress_trend", "")
        fb.ai_suggestions = data.get("ai_suggestions", "")
    except json.JSONDecodeError:
        fb.ai_suggestions = response

    await db.flush()
    return {"ok": True, "feedback": response}


@router.get("/{student_id}/dashboard")
async def dashboard(student_id: int, db: AsyncSession = Depends(get_db)):
    """首頁儀表盤數據"""
    student = await get_student_full(db, student_id)
    if not student:
        return {"error": "學生不存在"}

    # 各模組學習次數統計
    result = await db.execute(
        select(
            LearningRecord.module,
            func.count(LearningRecord.id).label("count"),
        )
        .where(LearningRecord.student_id == student_id)
        .group_by(LearningRecord.module)
    )
    module_stats = {row.module: row.count for row in result.all()}

    # 能力雷達圖數據
    ap = student.ability_profile
    radar_data = {}
    if ap:
        radar_data = {
            "academic": round((ap.chinese_score + ap.math_score + ap.english_score + ap.physics_score) / 4, 1),
            "expression": round((ap.logic_score + ap.language_score + ap.persuasion_score + ap.creativity_score) / 4, 1),
            "interview": round((ap.confidence_score + ap.responsiveness_score + ap.depth_score + ap.uniqueness_score) / 4, 1),
            "time_management": 50,
            "thinking": 50,
            "effort_strategy": 50,
            "uniqueness": 50,
        }

    return {
        "student_name": student.name,
        "module_stats": module_stats,
        "radar_data": radar_data,
        "interests_count": len(student.interests),
        "feedback_count": len(student.feedback_summaries),
    }
