"""選擇導航路由 - 尋找心中的巴拿馬"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import Goal
from schemas import GoalCreate, GoalOut
from services.ai_service import get_ai_response, get_ai_response_full
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.get("/{student_id}/goals", response_model=list[GoalOut])
async def list_goals(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Goal).where(Goal.student_id == student_id).order_by(Goal.created_at.desc())
    )
    return result.scalars().all()


@router.post("/{student_id}/goals", response_model=GoalOut)
async def create_goal(student_id: int, data: GoalCreate, db: AsyncSession = Depends(get_db)):
    goal = Goal(student_id=student_id, **data.model_dump())
    db.add(goal)
    await db.flush()
    await db.refresh(goal)
    return goal


@router.post("/{student_id}/explore-assumptions")
async def explore_assumptions(student_id: int, goal_id: int, db: AsyncSession = Depends(get_db)):
    """AI 識別隱含假設"""
    student = await get_student_full(db, student_id)
    if not student:
        return {"error": "學生不存在"}

    result = await db.execute(select(Goal).where(Goal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        return {"error": "目標不存在"}

    message = (
        f"我的目標是：{goal.title}\n"
        f"描述：{goal.description or '無'}\n"
        f"五年願景：{goal.five_year_vision or '尚未設定'}\n\n"
        f"請幫我識別這個目標背後可能存在的「隱含假設」——那些我不自覺的預設條件，"
        f"可能在束縛我的思維。同時，如果這個選擇讓我兩難，請幫我探索「第三選擇」。"
    )

    ctx = student_to_context(student)
    stream = await get_ai_response("choice_navigator", goal.scenario.value if goal.scenario else None, ctx, message)

    async def event_generator():
        full_response = ""
        async for chunk in stream:
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        # 保存識別結果
        goal.hidden_assumptions = full_response[:2000]
        await db.flush()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/decision-matrix")
async def decision_matrix(student_id: int, options: list[str], criteria: list[str], db: AsyncSession = Depends(get_db)):
    """精細化選擇矩陣 - AI 輔助多維度打分"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    options_str = "、".join(options)
    criteria_str = "、".join(criteria)
    message = (
        f"我面臨以下選擇：{options_str}\n"
        f"評估維度：{criteria_str}\n\n"
        f"請幫我用決策矩陣分析每個選項在各維度上的得分（1-10分），"
        f"並給出綜合建議。注意引導我從終極目標出發思考。"
    )

    stream = await get_ai_response("choice_navigator", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
