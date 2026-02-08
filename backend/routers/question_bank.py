"""題庫管理路由"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.connection import get_db
from database.models import Question
from schemas import QuestionCreate, QuestionOut
from typing import Optional
from services.ai_service import get_ai_response_full

router = APIRouter()


@router.get("/", response_model=list[QuestionOut])
async def list_questions(
    scenario: Optional[str] = None,
    difficulty: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(Question)
    if scenario:
        query = query.where(Question.scenario == scenario)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
    if subject:
        query = query.where(Question.subject == subject)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=QuestionOut)
async def create_question(data: QuestionCreate, db: AsyncSession = Depends(get_db)):
    question = Question(**data.model_dump())
    db.add(question)
    await db.flush()
    await db.refresh(question)
    return question


@router.post("/batch", response_model=list[QuestionOut])
async def create_questions_batch(data: list[QuestionCreate], db: AsyncSession = Depends(get_db)):
    questions = [Question(**d.model_dump()) for d in data]
    db.add_all(questions)
    await db.flush()
    for q in questions:
        await db.refresh(q)
    return questions


@router.get("/{question_id}", response_model=QuestionOut)
async def get_question(question_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Question).where(Question.id == question_id))
    q = result.scalar_one_or_none()
    if not q:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="題目不存在")
    return q


@router.post("/ai-generate")
async def ai_generate_questions(
    scenario: str,
    difficulty: str = "basic",
    subject: Optional[str] = None,
    count: int = 3,
    db: AsyncSession = Depends(get_db),
):
    """使用 AI 動態生成題目"""
    subject_hint = f"，學科為{subject}" if subject else ""
    prompt = (
        f"請為中學生生成{count}道{scenario}場景的{difficulty}難度練習題{subject_hint}。\n"
        f"請以 JSON 數組格式返回，每道題包含：title(題幹), options(選項列表,可為null), "
        f"reference_answer(參考答案), knowledge_tags(知識點標籤列表), solution_hint(解題思路)。\n"
        f"只返回 JSON，不要其他內容。"
    )

    response = await get_ai_response_full(
        module="learning_dojo",
        scenario=scenario,
        student_info=None,
        user_message=prompt,
    )

    return {"generated": response}
