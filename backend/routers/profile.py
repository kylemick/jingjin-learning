"""個人檔案管理路由"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.connection import get_db
from database.models import Student, AbilityProfile, InterestItem, FeedbackSummary
from schemas import (
    StudentCreate, StudentUpdate, StudentOut, InterestCreate,
    InterestItemOut, FeedbackSummaryOut, AbilityProfileOut,
)

router = APIRouter()


@router.post("/students", response_model=StudentOut)
async def create_student(data: StudentCreate, db: AsyncSession = Depends(get_db)):
    student = Student(**data.model_dump())
    db.add(student)
    await db.flush()
    # 自動創建能力畫像
    ability = AbilityProfile(student_id=student.id)
    db.add(ability)
    await db.flush()
    await db.refresh(student, ["ability_profile", "interests"])
    return student


@router.get("/students", response_model=list[StudentOut])
async def list_students(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student).options(
            selectinload(Student.ability_profile),
            selectinload(Student.interests),
        )
    )
    return result.scalars().all()


@router.get("/students/{student_id}", response_model=StudentOut)
async def get_student(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student)
        .options(
            selectinload(Student.ability_profile),
            selectinload(Student.interests),
        )
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")
    return student


@router.put("/students/{student_id}", response_model=StudentOut)
async def update_student(student_id: int, data: StudentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.ability_profile), selectinload(Student.interests))
        .where(Student.id == student_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="學生不存在")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(student, key, value)
    await db.flush()
    await db.refresh(student)
    return student


@router.post("/students/{student_id}/interests", response_model=InterestItemOut)
async def add_interest(student_id: int, data: InterestCreate, db: AsyncSession = Depends(get_db)):
    interest = InterestItem(student_id=student_id, **data.model_dump())
    db.add(interest)
    await db.flush()
    await db.refresh(interest)
    return interest


@router.delete("/students/{student_id}/interests/{interest_id}")
async def remove_interest(student_id: int, interest_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(InterestItem).where(
            InterestItem.id == interest_id,
            InterestItem.student_id == student_id,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
    return {"ok": True}


@router.get("/students/{student_id}/ability", response_model=AbilityProfileOut)
async def get_ability(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AbilityProfile).where(AbilityProfile.student_id == student_id)
    )
    ability = result.scalar_one_or_none()
    if not ability:
        raise HTTPException(status_code=404, detail="能力畫像不存在")
    return ability


@router.get("/students/{student_id}/feedback-summaries", response_model=list[FeedbackSummaryOut])
async def get_feedback_summaries(student_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(FeedbackSummary).where(FeedbackSummary.student_id == student_id)
    )
    return result.scalars().all()
