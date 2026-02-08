"""行動工坊路由 - 即刻行動"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import ActionPlan, LearningRecord, Question
from schemas import ActionPlanCreate, ActionPlanOut, LearningRecordCreate, LearningRecordOut
from services.ai_service import get_ai_response
from services.learning_engine import get_student_full, student_to_context, smart_recommend_questions
import json
from datetime import datetime

router = APIRouter()


@router.get("/{student_id}/plans", response_model=list[ActionPlanOut])
async def list_plans(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActionPlan).where(ActionPlan.student_id == student_id).order_by(ActionPlan.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{student_id}/plans", response_model=ActionPlanOut)
async def create_plan(student_id: int, data: ActionPlanCreate, db: AsyncSession = Depends(get_db)):
    plan = ActionPlan(student_id=student_id, **data.model_dump())
    db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.post("/{student_id}/decompose-task")
async def decompose_task(student_id: int, task_description: str, db: AsyncSession = Depends(get_db)):
    """圖層工作法 - AI 分解任務"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"我要完成以下任務：{task_description}\n\n"
        f"請用「圖層工作法」幫我分解這個任務：\n"
        f"1. 核心區間（最重要的核心思考部分）\n"
        f"2. 支撐區間（細節和輔助部分）\n"
        f"3. MVP 版本（最小可行的第一步是什麼？）\n"
        f"請具體化每一步，讓我可以「即刻行動」。"
    )

    stream = await get_ai_response("action_workshop", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/{student_id}/recommend-questions")
async def recommend_questions(student_id: int, scenario: str, db: AsyncSession = Depends(get_db)):
    """智能推薦題目"""
    questions = await smart_recommend_questions(db, student_id, scenario)
    return [
        {
            "id": q.id, "title": q.title, "difficulty": q.difficulty.value if q.difficulty else "basic",
            "question_type": q.question_type, "options": q.options,
        }
        for q in questions
    ]


@router.post("/{student_id}/submit-practice")
async def submit_practice(student_id: int, data: LearningRecordCreate, db: AsyncSession = Depends(get_db)):
    """提交練習並獲取 AI 即時反饋"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    # 如果有關聯題目，獲取題目信息
    question_info = ""
    if data.question_id:
        result = await db.execute(select(Question).where(Question.id == data.question_id))
        q = result.scalar_one_or_none()
        if q:
            question_info = f"題目：{q.title}\n參考答案：{q.reference_answer or '無'}\n"

    message = (
        f"{question_info}"
        f"學生的回答/練習內容：{data.content}\n\n"
        f"請給出具體的評估和反饋，包括：\n"
        f"1. 回答的優點\n"
        f"2. 可以改進的地方\n"
        f"3. 建議的下一步學習方向"
    )

    # 創建學習記錄
    record = LearningRecord(
        student_id=student_id,
        module=data.module,
        scenario=data.scenario,
        question_id=data.question_id,
        content=data.content,
        duration_minutes=data.duration_minutes,
    )
    db.add(record)
    await db.flush()

    stream = await get_ai_response("action_workshop", data.scenario, ctx, message)

    async def event_generator():
        full_response = ""
        async for chunk in stream:
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        # 保存 AI 反饋
        record.ai_feedback = full_response
        await db.flush()
        yield f"data: {json.dumps({'record_id': record.id}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.put("/{student_id}/plans/{plan_id}/complete")
async def complete_plan(student_id: int, plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ActionPlan).where(ActionPlan.id == plan_id, ActionPlan.student_id == student_id)
    )
    plan = result.scalar_one_or_none()
    if plan:
        plan.status = "completed"
        plan.completed_at = datetime.utcnow()
        await db.flush()
    return {"ok": True}
