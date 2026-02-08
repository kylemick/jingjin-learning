"""學習道場路由 - 直面現實的學習"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.ai_service import get_ai_response
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.post("/{student_id}/question-centered-learning")
async def question_centered_learning(
    student_id: int,
    topic: str,
    scenario: str = "academic",
    db: AsyncSession = Depends(get_db),
):
    """以問題為中心的學習 - AI 引導提問"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"我想學習關於「{topic}」的知識。\n\n"
        f"請用「以問題為中心」的方式引導我學習：\n"
        f"1. 先幫我提出 3-5 個關於這個主題的好問題（由淺入深）\n"
        f"2. 引導我自己思考這些問題的答案\n"
        f"3. 不要直接告訴我答案，而是通過提問讓我自己發現\n"
        f"記住：好的學習者，首先要向自己提問。"
    )

    stream = await get_ai_response("learning_dojo", scenario, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/decode-knowledge")
async def decode_knowledge(
    student_id: int,
    content: str,
    scenario: str = "academic",
    db: AsyncSession = Depends(get_db),
):
    """知識解碼 - 從信息到知識到技能"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"以下是我學到的內容：\n{content}\n\n"
        f"請幫我進行「知識解碼」三層分析：\n"
        f"1. 【信息層】這段內容的核心事實是什麼？\n"
        f"2. 【知識層】背後的原理和規律是什麼？為什麼是這樣？\n"
        f"3. 【技能層】我可以怎麼應用這些知識？能解決什麼實際問題？\n"
        f"4. 【融合層】這些知識和我已有的知識有什麼關聯？能產生什麼「化學反應」？\n\n"
        f"記住：不要只做信息的搬運工，要深入到事物的深層。"
    )

    stream = await get_ai_response("learning_dojo", scenario, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/knowledge-fusion")
async def knowledge_fusion(
    student_id: int,
    knowledge_a: str,
    knowledge_b: str,
    db: AsyncSession = Depends(get_db),
):
    """知識融合 - 跨學科知識關聯訓練"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"我學了兩個看似不相關的知識：\n"
        f"知識A：{knowledge_a}\n"
        f"知識B：{knowledge_b}\n\n"
        f"請引導我發現這兩個知識之間的深層關聯：\n"
        f"1. 它們有什麼共同的底層結構或原理嗎？\n"
        f"2. 把它們結合起來能產生什麼新的理解？\n"
        f"3. 這種融合能幫助我解決什麼新問題？\n\n"
        f"讓分離的知識產生化學反應！"
    )

    stream = await get_ai_response("learning_dojo", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
