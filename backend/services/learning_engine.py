"""
精進學習引擎 - 核心業務邏輯
負責個人檔案上下文構建、能力評估更新等
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import (
    Student, AbilityProfile, FeedbackSummary, InterestItem,
    LearningRecord, Question
)
from typing import Optional


async def get_student_full(db: AsyncSession, student_id: int) -> Optional[Student]:
    """獲取學生完整檔案（含所有關聯數據）"""
    result = await db.execute(
        select(Student)
        .options(
            selectinload(Student.ability_profile),
            selectinload(Student.interests),
            selectinload(Student.feedback_summaries),
        )
        .where(Student.id == student_id)
    )
    return result.scalar_one_or_none()


def student_to_context(student: Student) -> dict:
    """將 Student ORM 對象轉換為 AI Prompt 上下文字典"""
    ctx = {
        "name": student.name,
        "grade": student.grade,
        "school": student.school,
        "target_direction": student.target_direction,
        "personality": student.personality,
        "learning_style": student.learning_style,
    }

    if student.ability_profile:
        ap = student.ability_profile
        ctx["ability_profile"] = {
            "chinese_score": ap.chinese_score,
            "math_score": ap.math_score,
            "english_score": ap.english_score,
            "physics_score": ap.physics_score,
            "chemistry_score": ap.chemistry_score,
            "biology_score": ap.biology_score,
            "history_score": ap.history_score,
            "geography_score": ap.geography_score,
            "politics_score": ap.politics_score,
            "logic_score": ap.logic_score,
            "language_score": ap.language_score,
            "persuasion_score": ap.persuasion_score,
            "creativity_score": ap.creativity_score,
            "confidence_score": ap.confidence_score,
            "responsiveness_score": ap.responsiveness_score,
            "depth_score": ap.depth_score,
            "uniqueness_score": ap.uniqueness_score,
        }

    ctx["interests"] = [
        {"topic": i.topic, "depth": i.depth, "category": i.category}
        for i in (student.interests or [])
    ]

    ctx["feedback_summaries"] = [
        {
            "scenario": fb.scenario.value if fb.scenario else "",
            "strengths": fb.strengths,
            "weaknesses": fb.weaknesses,
            "progress_trend": fb.progress_trend,
        }
        for fb in (student.feedback_summaries or [])
    ]

    return ctx


async def smart_recommend_questions(
    db: AsyncSession,
    student_id: int,
    scenario: str,
    limit: int = 5,
) -> list:
    """根據學生能力畫像智能推薦題目"""
    student = await get_student_full(db, student_id)
    if not student or not student.ability_profile:
        # 沒有能力畫像，返回基礎題目
        result = await db.execute(
            select(Question)
            .where(Question.scenario == scenario)
            .where(Question.difficulty == "basic")
            .limit(limit)
        )
        return result.scalars().all()

    # 根據能力畫像選擇難度
    ap = student.ability_profile
    if scenario == "academic":
        avg = (ap.chinese_score + ap.math_score + ap.english_score) / 3
    elif scenario == "expression":
        avg = (ap.logic_score + ap.language_score + ap.persuasion_score + ap.creativity_score) / 4
    else:
        avg = (ap.confidence_score + ap.responsiveness_score + ap.depth_score + ap.uniqueness_score) / 4

    # 「必要的難度」：選擇略高於當前水平的題目
    if avg < 40:
        difficulty = "basic"
    elif avg < 70:
        difficulty = "intermediate"
    else:
        difficulty = "challenge"

    result = await db.execute(
        select(Question)
        .where(Question.scenario == scenario)
        .where(Question.difficulty == difficulty)
        .limit(limit)
    )
    return result.scalars().all()
